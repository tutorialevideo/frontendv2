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
        Include mai multe variații de denumire pentru matching mai bun
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
            
            # Index by multiple name variations
            for name_field in ['denumire', 'anaf_denumire', 'mf_denumire']:
                name = firma.get(name_field)
                if not name:
                    continue
                
                # 1. Full normalized name
                normalized = self.normalize_text(name)
                self._add_to_index(normalized, cui)
                
                # 2. Clean company name (without SRL, SA, etc.)
                clean_name = self.normalize_company_name(name)
                if clean_name and clean_name != normalized:
                    self._add_to_index(clean_name, cui)
                
                # 3. Without "SC" prefix if present
                if normalized.startswith('sc '):
                    self._add_to_index(normalized[3:], cui)
                
                # 4. First word(s) for partial matching
                words = clean_name.split()
                if len(words) >= 2:
                    self._add_to_index(' '.join(words[:2]), cui)
                if len(words) >= 1 and len(words[0]) >= 4:
                    self._add_to_index(words[0], cui)
            
            count += 1
            if count % 100000 == 0:
                logger.info(f"Indexed {count} companies...")
        
        logger.info(f"Firma index built: {len(self.firme_cache)} companies, {len(self.denumire_index)} name variations")
    
    def _add_to_index(self, name: str, cui: str):
        """Helper to add name to index"""
        if not name or len(name) < 2:
            return
        if name not in self.denumire_index:
            self.denumire_index[name] = []
        if cui not in self.denumire_index[name]:
            self.denumire_index[name].append(cui)
    
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
        Extrage toate părțile din dosar - adaptat pentru Portal JUST
        Structură: { "parti": [{ "nume": "...", "calitateParte": "..." }] }
        """
        parti = []
        
        # Direct extraction from 'parti' array
        if 'parti' in dosar and isinstance(dosar['parti'], list):
            for parte in dosar['parti']:
                if isinstance(parte, dict) and 'nume' in parte:
                    parti.append({
                        "nume": parte.get('nume', ''),
                        "rol": parte.get('calitateParte', ''),
                        "is_firma": self.is_company_name(parte.get('nume', ''))
                    })
        
        return parti
    
    def is_company_name(self, name: str) -> bool:
        """
        Verifică dacă un nume este o firmă (SRL, SA, PFA, etc.)
        """
        if not name:
            return False
        
        name_upper = name.upper()
        
        # Indicatori de firmă
        company_indicators = [
            'S.R.L', 'SRL', 'S.R.L.', 
            'S.A.', 'S.A', 'SA',
            'S.C.', 'S.C', 'SC',
            'P.F.A', 'PFA', 'P.F.A.',
            'I.I.', 'II', 'I.F.', 'IF',
            'S.N.C', 'SNC', 'S.C.S', 'SCS', 'S.C.A', 'SCA',
            'O.N.G', 'ONG', 'ASOCIATIA', 'ASOCIAȚIA', 'FUNDATIA', 'FUNDAȚIA',
            'R.A.', 'RA', 'REGIA',
            'COOP', 'COOPERATIVA',
            'BANCA', 'BANK',
            'COMPANIA', 'COMPANY', 'SOCIETATE',
            'GRUP', 'GROUP', 'HOLDING',
            'LTD', 'LLC', 'GMBH', 'INC',
        ]
        
        for indicator in company_indicators:
            if indicator in name_upper:
                return True
        
        return False
    
    def normalize_company_name(self, name: str) -> str:
        """
        Normalizează numele firmei pentru matching
        "S.C. S.O.S. UTILAJE CO S.R.L." -> "sos utilaje co"
        """
        if not name:
            return ""
        
        # Start with basic normalization
        name = self.normalize_text(name)
        
        # Remove common prefixes
        prefixes_to_remove = [
            'sc ', 's c ', 'societatea comerciala ', 'societatea ',
        ]
        for prefix in prefixes_to_remove:
            if name.startswith(prefix):
                name = name[len(prefix):]
        
        # Remove common suffixes (forma juridică)
        suffixes_to_remove = [
            ' srl', ' s r l', ' sa', ' s a', ' pfa', ' p f a',
            ' ii', ' i i', ' if', ' i f', ' snc', ' s n c',
            ' scs', ' s c s', ' sca', ' s c a',
            ' ra', ' r a', ' coop', ' cooperativa',
            ' ong', ' asociatia', ' fundatia',
            ' ltd', ' llc', ' gmbh', ' inc',
        ]
        for suffix in suffixes_to_remove:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
        
        # Remove extra whitespace
        name = ' '.join(name.split())
        
        return name.strip()
    
    def match_parte(self, parte: dict) -> List[Tuple[dict, float, str]]:
        """
        Încearcă să facă match pentru o parte din dosar
        Returnează lista de (firma, score, match_type)
        
        Îmbunătățiri:
        - Skip persoane fizice (nu sunt firme)
        - Normalizare avansată pentru denumiri
        - Multiple strategii de matching
        """
        matches = []
        
        nume = parte.get('nume', '')
        is_firma = parte.get('is_firma', False)
        
        # Skip dacă nu e firmă (persoană fizică)
        if not is_firma:
            logger.debug(f"Skipping non-company: {nume}")
            return matches
        
        # Normalizează numele firmei
        nume_normalized = self.normalize_company_name(nume)
        nume_full_normalized = self.normalize_text(nume)
        
        logger.debug(f"Matching: '{nume}' -> normalized: '{nume_normalized}'")
        
        # Strategia 1: Match exact pe denumire normalizată
        if nume_normalized in self.denumire_index:
            for cui in self.denumire_index[nume_normalized]:
                firma = self.firme_cache.get(cui)
                if firma:
                    matches.append((firma, 1.0, 'exact_match'))
                    self.stats["match_by_name"] += 1
        
        # Strategia 2: Match pe denumire completă normalizată
        if not matches and nume_full_normalized in self.denumire_index:
            for cui in self.denumire_index[nume_full_normalized]:
                firma = self.firme_cache.get(cui)
                if firma:
                    matches.append((firma, 0.98, 'full_name_match'))
                    self.stats["match_by_name"] += 1
        
        # Strategia 3: Match pe cuvintele principale
        if not matches:
            words = nume_normalized.split()
            if len(words) >= 2:
                # Încearcă primele 2 cuvinte
                two_words = ' '.join(words[:2])
                if two_words in self.denumire_index:
                    for cui in self.denumire_index[two_words]:
                        firma = self.firme_cache.get(cui)
                        if firma:
                            # Verifică că nu e un false positive
                            firma_name = self.normalize_company_name(firma.get('denumire', ''))
                            score = self.fuzzy_match_score(nume_normalized, firma_name)
                            if score >= 0.7:
                                matches.append((firma, score, 'partial_match'))
                                self.stats["match_by_fuzzy"] += 1
        
        # Strategia 4: Fuzzy matching (mai lent, folosit doar dacă nu avem match)
        if not matches and len(nume_normalized) >= 5:
            candidates = []
            name_words = set(nume_normalized.split())
            
            # Caută prin index pentru candidați cu cuvinte comune
            for indexed_name, cuis in self.denumire_index.items():
                if len(indexed_name) < 3:
                    continue
                    
                indexed_words = set(indexed_name.split())
                common_words = name_words & indexed_words
                
                # Trebuie să aibă cel puțin un cuvânt comun semnificativ
                if common_words and any(len(w) >= 4 for w in common_words):
                    score = self.fuzzy_match_score(nume_normalized, indexed_name)
                    if score >= 0.75:
                        for cui in cuis:
                            candidates.append((cui, score, indexed_name))
            
            # Sortează și ia top 3
            candidates.sort(key=lambda x: x[1], reverse=True)
            seen_cuis = set()
            for cui, score, matched_name in candidates[:5]:
                if cui not in seen_cuis:
                    firma = self.firme_cache.get(cui)
                    if firma:
                        matches.append((firma, score, 'fuzzy_match'))
                        self.stats["match_by_fuzzy"] += 1
                        seen_cuis.add(cui)
        
        # Deduplicate matches
        unique_matches = []
        seen_cuis = set()
        for firma, score, match_type in matches:
            cui = str(firma.get('cui', ''))
            if cui not in seen_cuis:
                unique_matches.append((firma, score, match_type))
                seen_cuis.add(cui)
        
        return sorted(unique_matches, key=lambda x: x[1], reverse=True)
    
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
    
    def test_match_name(self, name: str):
        """
        Testează matching pentru o denumire de firmă
        """
        self.build_firma_index()
        
        print(f"\nTest matching pentru: '{name}'")
        print(f"Normalizat: '{self.normalize_company_name(name)}'")
        print(f"Este firmă: {self.is_company_name(name)}")
        print("-" * 50)
        
        # Simulăm o parte de dosar
        parte = {
            "nume": name,
            "rol": "test",
            "is_firma": self.is_company_name(name)
        }
        
        matches = self.match_parte(parte)
        
        if matches:
            print(f"Găsite {len(matches)} rezultate:\n")
            for i, (firma, score, match_type) in enumerate(matches, 1):
                print(f"  {i}. {firma.get('denumire')}")
                print(f"     CUI: {firma.get('cui')}")
                print(f"     Județ: {firma.get('judet')}")
                print(f"     Scor: {score:.2%}")
                print(f"     Tip match: {match_type}")
                print()
        else:
            print("Nu s-au găsit rezultate.")
    
    def test_match_file(self, file_path: str):
        """
        Testează matching pentru un fișier JSON specific
        """
        self.build_firma_index()
        
        print(f"\nProcesare fișier: {file_path}")
        print("=" * 60)
        
        results = self.process_json_file(file_path)
        
        for result in results:
            print(f"\nDosar: {result['numar_dosar']}")
            print(f"Instanță: {result['instanta']}")
            print(f"Obiect: {result['obiect']}")
            print("-" * 40)
            
            if result['parti_gasite']:
                print("Părți găsite:")
                for parte in result['parti_gasite']:
                    print(f"  • {parte['nume_original']} ({parte['rol']})")
                    if parte['matches']:
                        for match in parte['matches']:
                            print(f"    → {match['denumire']} (CUI: {match['cui']}, scor: {match['score']:.0%}, tip: {match['match_type']})")
                    else:
                        print(f"    → Fără match (probabil persoană fizică)")
            
            if result['firme_matched']:
                print(f"\nTotal firme identificate: {len(result['firme_matched'])}")
            print()
        
        print(f"\nStatistici:")
        for key, value in self.stats.items():
            print(f"  {key}: {value}")


def main():
    """
    Main entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Portal JUST Dosare Matcher')
    parser.add_argument('--path', '-p', type=str,
                        help='Calea către directorul cu fișiere JSON')
    parser.add_argument('--output', '-o', type=str, default='dosare_matched.json',
                        help='Fișierul output (default: dosare_matched.json)')
    parser.add_argument('--mongo-url', type=str, default='mongodb://localhost:27017/',
                        help='MongoDB connection URL')
    parser.add_argument('--db-name', type=str, default='mfirme_local',
                        help='Database name')
    parser.add_argument('--test-cui', type=str,
                        help='Testează matching pentru un CUI specific')
    parser.add_argument('--test-name', type=str,
                        help='Testează matching pentru o denumire de firmă')
    parser.add_argument('--test-file', type=str,
                        help='Testează matching pentru un fișier JSON specific')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Mod verbose (afișează mai multe detalii)')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    matcher = DosareMatcherImproved(
        mongo_url=args.mongo_url,
        db_name=args.db_name
    )
    
    if args.test_cui:
        matcher.test_match_cui(args.test_cui)
    elif args.test_name:
        matcher.test_match_name(args.test_name)
    elif args.test_file:
        matcher.test_match_file(args.test_file)
    elif args.path:
        matcher.process_directory(args.path, args.output)
    else:
        print("Folosire:")
        print("  1. Procesare director complet:")
        print("     python dosare_matcher.py --path /cale/catre/dosare --output rezultate.json")
        print("")
        print("  2. Test pentru o denumire de firmă:")
        print("     python dosare_matcher.py --test-name 'S.C. EXEMPLU SRL'")
        print("")
        print("  3. Test pentru un fișier JSON specific:")
        print("     python dosare_matcher.py --test-file /cale/catre/dosar.json")
        print("")
        print("  4. Mod verbose pentru debugging:")
        print("     python dosare_matcher.py --path /cale --verbose")


if __name__ == "__main__":
    main()
