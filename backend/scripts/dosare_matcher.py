"""
Portal JUST - Dosare Matching Script (Îmbunătățit)
Matching dosare civile cu firme din baza de date

Îmbunătățiri față de versiunea anterioară:
1. Fuzzy matching pe denumire (Levenshtein distance)
2. Normalizare CUI (cu/fără RO, spații, puncte)
3. Normalizare diacritice și caractere speciale
4. Căutare în TOATE părțile dosarului (reclamant, pârât, intervenient, etc.)
5. Matching pe fragmente de denumire
6. Scoring sistem pentru calitatea match-ului
7. Logging detaliat pentru debugging
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
from pymongo import MongoClient
from difflib import SequenceMatcher
import unicodedata

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dosare_match.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DosareMatcherImproved:
    """
    Matcher îmbunătățit pentru dosare Portal JUST
    """
    
    def __init__(self, mongo_url: str = "mongodb://localhost:27017/", db_name: str = "mfirme_local"):
        self.client = MongoClient(mongo_url)
        self.db = self.client[db_name]
        self.firme_cache: Dict[str, dict] = {}  # CUI -> firma
        self.denumire_index: Dict[str, List[str]] = {}  # normalized_name -> [CUI list]
        self.stats = {
            "total_dosare": 0,
            "matched_dosare": 0,
            "unmatched_dosare": 0,
            "total_parti_matched": 0,
            "match_by_cui": 0,
            "match_by_name": 0,
            "match_by_fuzzy": 0
        }
        
    def normalize_cui(self, cui: str) -> str:
        """
        Normalizează CUI pentru matching
        Exemple: 'RO37044065' -> '37044065', 'RO 37.044.065' -> '37044065'
        """
        if not cui:
            return ""
        
        # Convert to string
        cui = str(cui).strip().upper()
        
        # Remove RO prefix
        cui = re.sub(r'^RO\s*', '', cui)
        
        # Remove spaces, dots, dashes
        cui = re.sub(r'[\s.\-]', '', cui)
        
        # Keep only digits
        cui = re.sub(r'[^0-9]', '', cui)
        
        return cui
    
    def normalize_text(self, text: str) -> str:
        """
        Normalizează text pentru matching
        - Lowercase
        - Elimină diacritice
        - Elimină caractere speciale
        - Normalizează spații
        """
        if not text:
            return ""
        
        text = str(text).lower().strip()
        
        # Remove diacritics
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        # Replace common variations
        replacements = {
            'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ş': 's', 'ț': 't', 'ţ': 't',
            's.r.l.': 'srl', 's.r.l': 'srl', 'srl.': 'srl',
            's.a.': 'sa', 's.a': 'sa',
            'p.f.a.': 'pfa', 'p.f.a': 'pfa',
            'i.i.': 'ii', 'i.f.': 'if',
            'nr.': 'nr', 'str.': 'str', 'bl.': 'bl', 'sc.': 'sc', 'et.': 'et', 'ap.': 'ap',
            'municipiul': 'mun', 'localitatea': 'loc', 'judetul': 'jud',
            'sector': 'sect', 'bucuresti': 'bucuresti',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def extract_company_name(self, text: str) -> str:
        """
        Extrage numele firmei din text (elimină forma juridică de la sfârșit)
        """
        if not text:
            return ""
        
        text = self.normalize_text(text)
        
        # Remove common suffixes
        suffixes = ['srl', 'sa', 'pfa', 'ii', 'if', 'scs', 'sca', 'snc', 'ra', 'coop', 'ong', 'fundatia', 'asociatia']
        
        words = text.split()
        if words and words[-1] in suffixes:
            words = words[:-1]
        
        return ' '.join(words)
    
    def fuzzy_match_score(self, s1: str, s2: str) -> float:
        """
        Calculează scorul de similaritate între două stringuri (0-1)
        """
        if not s1 or not s2:
            return 0.0
        
        # Normalize both strings
        s1 = self.normalize_text(s1)
        s2 = self.normalize_text(s2)
        
        if s1 == s2:
            return 1.0
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, s1, s2).ratio()
    
    def extract_cui_from_text(self, text: str) -> List[str]:
        """
        Extrage toate CUI-urile posibile dintr-un text
        """
        if not text:
            return []
        
        # Pattern pentru CUI (cu sau fără RO)
        patterns = [
            r'(?:RO\s*)?(\d{6,10})',  # RO12345678 sau 12345678
            r'CUI[:\s]*(\d{6,10})',    # CUI: 12345678
            r'C\.?U\.?I\.?[:\s]*(\d{6,10})',  # C.U.I. 12345678
            r'cod\s*fiscal[:\s]*(\d{6,10})',  # cod fiscal 12345678
            r'J\d+/\d+/\d+',  # Nr. Registru Comerț
        ]
        
        cuis = set()
        for pattern in patterns:
            matches = re.findall(pattern, str(text), re.IGNORECASE)
            for match in matches:
                normalized = self.normalize_cui(match)
                if len(normalized) >= 6 and len(normalized) <= 10:
                    cuis.add(normalized)
        
        return list(cuis)
    
    def build_firma_index(self):
        """
        Construiește index-ul de firme pentru căutare rapidă
        """
        logger.info("Building firma index...")
        
        cursor = self.db.firme.find(
            {"cui": {"$exists": True}},
            {"cui": 1, "denumire": 1, "anaf_denumire": 1, "mf_denumire": 1, "judet": 1, "localitate": 1}
        )
        
        count = 0
        for firma in cursor:
            cui = self.normalize_cui(str(firma.get('cui', '')))
            if not cui:
                continue
            
            # Cache by CUI
            self.firme_cache[cui] = firma
            
            # Index by normalized name
            for name_field in ['denumire', 'anaf_denumire', 'mf_denumire']:
                name = firma.get(name_field)
                if name:
                    normalized = self.normalize_text(name)
                    if normalized not in self.denumire_index:
                        self.denumire_index[normalized] = []
                    if cui not in self.denumire_index[normalized]:
                        self.denumire_index[normalized].append(cui)
                    
                    # Also index the company name without suffix
                    clean_name = self.extract_company_name(name)
                    if clean_name and clean_name != normalized:
                        if clean_name not in self.denumire_index:
                            self.denumire_index[clean_name] = []
                        if cui not in self.denumire_index[clean_name]:
                            self.denumire_index[clean_name].append(cui)
            
            count += 1
            if count % 100000 == 0:
                logger.info(f"Indexed {count} companies...")
        
        logger.info(f"Firma index built: {len(self.firme_cache)} companies, {len(self.denumire_index)} name variations")
    
    def find_firma_by_cui(self, cui: str) -> Optional[dict]:
        """
        Găsește firma după CUI
        """
        normalized = self.normalize_cui(cui)
        return self.firme_cache.get(normalized)
    
    def find_firma_by_name(self, name: str, min_score: float = 0.85) -> List[Tuple[dict, float]]:
        """
        Găsește firme după nume cu fuzzy matching
        Returnează lista de (firma, score) sortată descrescător după scor
        """
        if not name:
            return []
        
        normalized = self.normalize_text(name)
        clean_name = self.extract_company_name(name)
        
        matches = []
        
        # Exact match
        if normalized in self.denumire_index:
            for cui in self.denumire_index[normalized]:
                firma = self.firme_cache.get(cui)
                if firma:
                    matches.append((firma, 1.0))
        
        # Clean name match
        if clean_name and clean_name != normalized and clean_name in self.denumire_index:
            for cui in self.denumire_index[clean_name]:
                firma = self.firme_cache.get(cui)
                if firma and (firma, 1.0) not in matches:
                    matches.append((firma, 0.98))
        
        # Fuzzy match (doar dacă nu avem match exact)
        if not matches:
            # Search through index (limited to prevent slowness)
            candidates = []
            name_words = set(normalized.split())
            
            for indexed_name, cuis in self.denumire_index.items():
                # Quick filter: at least one common word
                indexed_words = set(indexed_name.split())
                if name_words & indexed_words:
                    score = self.fuzzy_match_score(normalized, indexed_name)
                    if score >= min_score:
                        for cui in cuis:
                            candidates.append((cui, score))
            
            # Get top matches
            candidates.sort(key=lambda x: x[1], reverse=True)
            for cui, score in candidates[:5]:
                firma = self.firme_cache.get(cui)
                if firma:
                    matches.append((firma, score))
        
        # Sort by score
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def extract_parti_from_dosar(self, dosar: dict) -> List[dict]:
        """
        Extrage toate părțile din dosar
        Adaptează această funcție la structura JSON-ului tău
        """
        parti = []
        
        # Câmpuri comune pentru părți în dosare Portal JUST
        parti_fields = [
            'parti', 'partile', 'parties',
            'reclamant', 'reclamanti', 'plaintiff', 'plaintiffs',
            'parat', 'parati', 'pârât', 'pârâți', 'defendant', 'defendants',
            'intervenient', 'intervenienti',
            'creditor', 'creditori',
            'debitor', 'debitori',
            'contestator', 'contestatori',
            'intimat', 'intimati',
            'apelant', 'apelanti',
            'recurent', 'recurenti',
            'petent', 'petenti',
        ]
        
        for field in parti_fields:
            value = dosar.get(field)
            if value:
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            parti.append(item)
                        elif isinstance(item, str):
                            parti.append({"nume": item, "rol": field})
                elif isinstance(value, dict):
                    parti.append(value)
                elif isinstance(value, str):
                    # Parse string to extract multiple parties
                    for part in re.split(r'[,;]|\s+si\s+|\s+și\s+', value):
                        part = part.strip()
                        if part and len(part) > 3:
                            parti.append({"nume": part, "rol": field})
        
        # Verifică și în sub-obiecte
        for key, value in dosar.items():
            if isinstance(value, dict):
                nested_parti = self.extract_parti_from_dosar(value)
                parti.extend(nested_parti)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        # Check if this looks like a party
                        if any(k in str(item.keys()).lower() for k in ['nume', 'name', 'denumire', 'parte', 'party']):
                            parti.append(item)
        
        return parti
    
    def match_parte(self, parte: dict) -> List[Tuple[dict, float, str]]:
        """
        Încearcă să facă match pentru o parte din dosar
        Returnează lista de (firma, score, match_type)
        """
        matches = []
        
        # Extrage informații din parte
        nume = parte.get('nume') or parte.get('name') or parte.get('denumire') or ''
        cui = parte.get('cui') or parte.get('cif') or parte.get('cod_fiscal') or ''
        
        # Încearcă mai întâi match pe CUI
        if cui:
            firma = self.find_firma_by_cui(cui)
            if firma:
                matches.append((firma, 1.0, 'cui_exact'))
                self.stats["match_by_cui"] += 1
                return matches
        
        # Extrage CUI din text
        text_fields = [str(v) for v in parte.values() if v]
        full_text = ' '.join(text_fields)
        extracted_cuis = self.extract_cui_from_text(full_text)
        
        for extracted_cui in extracted_cuis:
            firma = self.find_firma_by_cui(extracted_cui)
            if firma:
                matches.append((firma, 0.95, 'cui_extracted'))
                self.stats["match_by_cui"] += 1
        
        if matches:
            return matches
        
        # Match pe nume
        if nume:
            name_matches = self.find_firma_by_name(nume, min_score=0.80)
            for firma, score in name_matches[:3]:  # Top 3
                match_type = 'name_exact' if score >= 0.98 else 'name_fuzzy'
                matches.append((firma, score, match_type))
                
                if score >= 0.98:
                    self.stats["match_by_name"] += 1
                else:
                    self.stats["match_by_fuzzy"] += 1
        
        return matches
    
    def process_dosar(self, dosar: dict) -> dict:
        """
        Procesează un dosar și găsește toate firmele din părți
        """
        result = {
            "numar_dosar": dosar.get('numar') or dosar.get('numar_dosar') or dosar.get('number') or 'unknown',
            "instanta": dosar.get('instanta') or dosar.get('court') or '',
            "data": dosar.get('data') or dosar.get('date') or '',
            "obiect": dosar.get('obiect') or dosar.get('object') or '',
            "parti_gasite": [],
            "firme_matched": [],
            "match_quality": "none"
        }
        
        parti = self.extract_parti_from_dosar(dosar)
        
        for parte in parti:
            matches = self.match_parte(parte)
            
            parte_info = {
                "nume_original": parte.get('nume') or parte.get('name') or parte.get('denumire') or str(parte),
                "rol": parte.get('rol') or parte.get('role') or '',
                "cui_original": parte.get('cui') or parte.get('cif') or '',
                "matches": []
            }
            
            for firma, score, match_type in matches:
                match_info = {
                    "cui": firma.get('cui'),
                    "denumire": firma.get('denumire') or firma.get('anaf_denumire'),
                    "score": score,
                    "match_type": match_type
                }
                parte_info["matches"].append(match_info)
                
                # Add to firme_matched if not already there
                if match_info not in result["firme_matched"]:
                    result["firme_matched"].append(match_info)
            
            result["parti_gasite"].append(parte_info)
        
        # Determine overall match quality
        if result["firme_matched"]:
            best_score = max(m["score"] for m in result["firme_matched"])
            if best_score >= 0.98:
                result["match_quality"] = "high"
            elif best_score >= 0.90:
                result["match_quality"] = "medium"
            else:
                result["match_quality"] = "low"
            self.stats["matched_dosare"] += 1
            self.stats["total_parti_matched"] += len(result["firme_matched"])
        else:
            self.stats["unmatched_dosare"] += 1
        
        self.stats["total_dosare"] += 1
        
        return result
    
    def process_json_file(self, file_path: str) -> List[dict]:
        """
        Procesează un fișier JSON cu dosare
        """
        results = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle both single dosar and list of dosare
            if isinstance(data, list):
                for dosar in data:
                    results.append(self.process_dosar(dosar))
            elif isinstance(data, dict):
                # Check if it's a wrapper with dosare inside
                if 'dosare' in data:
                    for dosar in data['dosare']:
                        results.append(self.process_dosar(dosar))
                else:
                    results.append(self.process_dosar(data))
                    
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
        
        return results
    
    def process_directory(self, base_path: str, output_file: str = "dosare_matched.json"):
        """
        Procesează toate fișierele JSON dintr-un director recursiv
        """
        logger.info(f"Processing dosare from: {base_path}")
        
        # Build index first
        self.build_firma_index()
        
        all_results = []
        json_files = list(Path(base_path).rglob("*.json"))
        
        logger.info(f"Found {len(json_files)} JSON files")
        
        for i, file_path in enumerate(json_files):
            if (i + 1) % 100 == 0:
                logger.info(f"Processing file {i+1}/{len(json_files)}...")
            
            results = self.process_json_file(str(file_path))
            for result in results:
                result["source_file"] = str(file_path)
                all_results.append(result)
        
        # Save results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "stats": self.stats,
                "results": all_results
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n=== STATISTICI FINALE ===")
        logger.info(f"Total dosare procesate: {self.stats['total_dosare']}")
        logger.info(f"Dosare cu match: {self.stats['matched_dosare']} ({self.stats['matched_dosare']/max(1,self.stats['total_dosare'])*100:.1f}%)")
        logger.info(f"Dosare fără match: {self.stats['unmatched_dosare']}")
        logger.info(f"Total părți matched: {self.stats['total_parti_matched']}")
        logger.info(f"Match by CUI: {self.stats['match_by_cui']}")
        logger.info(f"Match by Name (exact): {self.stats['match_by_name']}")
        logger.info(f"Match by Name (fuzzy): {self.stats['match_by_fuzzy']}")
        logger.info(f"\nResults saved to: {output_file}")
        
        return all_results
    
    def test_match_cui(self, cui: str):
        """
        Testează matching pentru un CUI specific
        """
        self.build_firma_index()
        
        firma = self.find_firma_by_cui(cui)
        if firma:
            print(f"\nFirma găsită pentru CUI {cui}:")
            print(f"  Denumire: {firma.get('denumire')}")
            print(f"  Județ: {firma.get('judet')}")
        else:
            print(f"\nNu s-a găsit firma pentru CUI {cui}")
        
        return firma


def main():
    """
    Main entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Portal JUST Dosare Matcher')
    parser.add_argument('--path', '-p', type=str, required=True,
                        help='Calea către directorul cu fișiere JSON')
    parser.add_argument('--output', '-o', type=str, default='dosare_matched.json',
                        help='Fișierul output (default: dosare_matched.json)')
    parser.add_argument('--mongo-url', type=str, default='mongodb://localhost:27017/',
                        help='MongoDB connection URL')
    parser.add_argument('--db-name', type=str, default='mfirme_local',
                        help='Database name')
    parser.add_argument('--test-cui', type=str,
                        help='Testează matching pentru un CUI specific')
    
    args = parser.parse_args()
    
    matcher = DosareMatcherImproved(
        mongo_url=args.mongo_url,
        db_name=args.db_name
    )
    
    if args.test_cui:
        matcher.test_match_cui(args.test_cui)
    else:
        matcher.process_directory(args.path, args.output)


if __name__ == "__main__":
    main()
