import React, { useState, useEffect } from 'react';
import { 
  Scale, 
  FileText, 
  AlertTriangle,
  Calendar,
  Building,
  Users,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Gavel,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

const LegalInfo = ({ cui }) => {
  const [summary, setSummary] = useState(null);
  const [dosare, setDosare] = useState([]);
  const [bpiRecords, setBpiRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedDosar, setExpandedDosar] = useState(null);
  const [showAllDosare, setShowAllDosare] = useState(false);
  const [showAllBpi, setShowAllBpi] = useState(false);

  const API_URL = process.env.REACT_APP_BACKEND_URL || '';

  useEffect(() => {
    const fetchLegalInfo = async () => {
      if (!cui) return;
      
      setLoading(true);
      try {
        // Fetch summary first
        const summaryRes = await fetch(`${API_URL}/api/legal/summary/${cui}`);
        if (summaryRes.ok) {
          const summaryData = await summaryRes.json();
          setSummary(summaryData);
          
          // Fetch dosare if any
          if (summaryData.dosare_count > 0) {
            const dosareRes = await fetch(`${API_URL}/api/legal/dosare/${cui}?limit=10`);
            if (dosareRes.ok) {
              const dosareData = await dosareRes.json();
              setDosare(dosareData.dosare || []);
            }
          }
          
          // Fetch BPI if any
          if (summaryData.bpi_count > 0) {
            const bpiRes = await fetch(`${API_URL}/api/legal/bpi/${cui}?limit=10`);
            if (bpiRes.ok) {
              const bpiData = await bpiRes.json();
              setBpiRecords(bpiData.records || []);
            }
          }
        }
        setError(null);
      } catch (err) {
        setError('Eroare la încărcarea informațiilor juridice');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchLegalInfo();
  }, [cui, API_URL]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('ro-RO');
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
          <span className="text-muted-foreground">Se încarcă informațiile juridice...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 text-red-500">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  if (!summary || (!summary.dosare_count && !summary.bpi_count)) {
    return (
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-green-500" />
          <div>
            <h3 className="font-semibold">Fără probleme juridice înregistrate</h3>
            <p className="text-sm text-muted-foreground">
              Nu s-au găsit dosare sau înregistrări BPI pentru această firmă
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="legal-info">
      {/* Summary Card */}
      <div className={`rounded-xl p-6 ${
        summary.in_insolventa 
          ? 'bg-red-500/10 border-2 border-red-500/50' 
          : summary.has_legal_issues 
            ? 'bg-amber-500/10 border border-amber-500/30'
            : 'bg-card border border-border'
      }`}>
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-lg ${
            summary.in_insolventa ? 'bg-red-500/20' : 'bg-amber-500/20'
          }`}>
            {summary.in_insolventa ? (
              <AlertTriangle className="w-6 h-6 text-red-600" />
            ) : (
              <Scale className="w-6 h-6 text-amber-600" />
            )}
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-lg">
              {summary.in_insolventa ? 'Firmă în Insolvență' : 'Informații Juridice'}
            </h3>
            {summary.stare && (
              <p className={`text-sm mt-1 ${summary.in_insolventa ? 'text-red-600 font-medium' : 'text-muted-foreground'}`}>
                Stare: {summary.stare}
              </p>
            )}
            <div className="flex flex-wrap gap-4 mt-3">
              <div className="flex items-center gap-2">
                <Gavel className="w-4 h-4 text-muted-foreground" />
                <span className="font-medium">{summary.dosare_count}</span>
                <span className="text-sm text-muted-foreground">dosare</span>
              </div>
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-muted-foreground" />
                <span className="font-medium">{summary.bpi_count}</span>
                <span className="text-sm text-muted-foreground">înregistrări BPI</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Dosare Section */}
      {dosare.length > 0 && (
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="p-4 border-b border-border bg-secondary/30">
            <h3 className="font-semibold flex items-center gap-2">
              <Gavel className="w-5 h-5 text-primary" />
              Dosare ({summary.dosare_count})
            </h3>
          </div>
          <div className="divide-y divide-border">
            {(showAllDosare ? dosare : dosare.slice(0, 5)).map((dosar, index) => (
              <div key={dosar.id || index} className="p-4">
                <div 
                  className="flex items-start justify-between cursor-pointer"
                  onClick={() => setExpandedDosar(expandedDosar === index ? null : index)}
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono font-medium text-primary">
                        {dosar.numar_dosar}
                      </span>
                      {dosar.stadiu && (
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded-full">
                          {dosar.stadiu}
                        </span>
                      )}
                      {dosar.calitate_parte && (
                        <span className={`px-2 py-0.5 text-xs rounded-full ${
                          dosar.calitate_parte.toLowerCase().includes('pârât') 
                            ? 'bg-red-100 text-red-700'
                            : 'bg-green-100 text-green-700'
                        }`}>
                          {dosar.calitate_parte}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {dosar.obiect}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Building className="w-3 h-3" />
                        {dosar.institutie}
                      </span>
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {formatDate(dosar.data_dosar)}
                      </span>
                    </div>
                  </div>
                  <button className="p-1 hover:bg-secondary rounded">
                    {expandedDosar === index ? (
                      <ChevronUp className="w-5 h-5" />
                    ) : (
                      <ChevronDown className="w-5 h-5" />
                    )}
                  </button>
                </div>
                
                {/* Expanded details */}
                {expandedDosar === index && (
                  <div className="mt-4 pt-4 border-t border-border space-y-3" data-testid={`dosar-details-${index}`}>
                    {/* Informații de bază dosar */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {dosar.categorie && (
                        <p className="text-sm">
                          <span className="text-muted-foreground">Categorie:</span>{' '}
                          <span className="font-medium">{dosar.categorie}</span>
                        </p>
                      )}
                      {dosar.stadiu && (
                        <p className="text-sm">
                          <span className="text-muted-foreground">Stadiu:</span>{' '}
                          <span className="font-medium">{dosar.stadiu}</span>
                        </p>
                      )}
                      {dosar.materie && (
                        <p className="text-sm">
                          <span className="text-muted-foreground">Materie:</span>{' '}
                          <span className="font-medium">{dosar.materie}</span>
                        </p>
                      )}
                      {dosar.departament && (
                        <p className="text-sm">
                          <span className="text-muted-foreground">Departament:</span>{' '}
                          <span className="font-medium">{dosar.departament}</span>
                        </p>
                      )}
                      {dosar.data_modificare && (
                        <p className="text-sm">
                          <span className="text-muted-foreground">Ultima actualizare:</span>{' '}
                          <span className="font-medium">{formatDate(dosar.data_modificare)}</span>
                        </p>
                      )}
                    </div>
                    
                    {/* Părți */}
                    {dosar.parti && dosar.parti.length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-2 flex items-center gap-1">
                          <Users className="w-4 h-4 text-muted-foreground" />
                          Părți implicate:
                        </p>
                        <div className="space-y-1 ml-5">
                          {dosar.parti.map((parte, i) => (
                            <div key={i} className="text-sm flex items-center gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-primary/60 shrink-0"></span>
                              <span>{parte.nume || parte.name}</span>
                              {(parte.calitateParte || parte.calitate) && (
                                <span className="text-xs text-muted-foreground px-1.5 py-0.5 bg-secondary rounded">
                                  {parte.calitateParte || parte.calitate}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Ședințe recente - Timeline */}
                    {dosar.sedinte && dosar.sedinte.length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-2 flex items-center gap-1">
                          <Calendar className="w-4 h-4 text-muted-foreground" />
                          Ședințe recente:
                        </p>
                        <div className="ml-5 border-l-2 border-primary/20 pl-4 space-y-3">
                          {dosar.sedinte.slice(0, 5).map((sedinta, i) => (
                            <div key={i} className="relative text-sm">
                              <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-primary/60 border-2 border-background"></div>
                              <div className="bg-secondary/50 p-3 rounded-lg">
                                <div className="flex justify-between items-start flex-wrap gap-1">
                                  <span className="font-medium text-primary">
                                    {formatDate(sedinta.data)} {sedinta.ora && `- ${sedinta.ora}`}
                                  </span>
                                  {sedinta.complet && (
                                    <span className="text-xs text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">
                                      Complet: {sedinta.complet}
                                    </span>
                                  )}
                                </div>
                                {sedinta.solutie && (
                                  <p className="text-foreground mt-1 font-medium">
                                    {sedinta.solutie}
                                  </p>
                                )}
                                {sedinta.solutieSumar && (
                                  <p className="text-muted-foreground mt-0.5 text-xs leading-relaxed">
                                    {sedinta.solutieSumar}
                                  </p>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Mesaj când nu sunt detalii suplimentare */}
                    {(!dosar.parti || dosar.parti.length === 0) && (!dosar.sedinte || dosar.sedinte.length === 0) && !dosar.departament && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground bg-secondary/30 p-3 rounded-lg">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>
                          {dosar.categorie || dosar.stadiu || dosar.materie
                            ? 'Părțile și ședințele nu sunt încă disponibile pentru acest dosar.'
                            : 'Detalii suplimentare nu sunt disponibile momentan. Datele vor fi actualizate la următoarea sincronizare.'
                          }
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
          {dosare.length > 5 && (
            <div className="p-4 border-t border-border text-center">
              <button
                onClick={() => setShowAllDosare(!showAllDosare)}
                className="text-primary hover:underline text-sm"
              >
                {showAllDosare ? 'Arată mai puțin' : `Arată toate (${dosare.length})`}
              </button>
            </div>
          )}
        </div>
      )}

      {/* BPI Section */}
      {bpiRecords.length > 0 && (
        <div className="bg-card border border-red-200 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-red-200 bg-red-50">
            <h3 className="font-semibold flex items-center gap-2 text-red-700">
              <AlertTriangle className="w-5 h-5" />
              Buletinul Procedurilor de Insolvență ({summary.bpi_count})
            </h3>
          </div>
          <div className="divide-y divide-red-100">
            {(showAllBpi ? bpiRecords : bpiRecords.slice(0, 5)).map((record, index) => (
              <div key={record.id || index} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      {record.tip_procedura && (
                        <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded-full">
                          {record.tip_procedura}
                        </span>
                      )}
                      {record.etapa_procedura && (
                        <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs rounded-full">
                          {record.etapa_procedura}
                        </span>
                      )}
                    </div>
                    {record.numar_dosar && (
                      <p className="font-mono text-sm mt-2">
                        Dosar: {record.numar_dosar}
                      </p>
                    )}
                    {record.descriere && (
                      <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                        {record.descriere}
                      </p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      {record.instanta && (
                        <span className="flex items-center gap-1">
                          <Building className="w-3 h-3" />
                          {record.instanta}
                        </span>
                      )}
                      {record.data_publicare && (
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(record.data_publicare)}
                        </span>
                      )}
                      {record.practician && (
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {record.practician}
                        </span>
                      )}
                    </div>
                  </div>
                  {record.url && (
                    <a 
                      href={record.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 hover:bg-secondary rounded"
                    >
                      <ExternalLink className="w-4 h-4 text-muted-foreground" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
          {bpiRecords.length > 5 && (
            <div className="p-4 border-t border-red-200 text-center">
              <button
                onClick={() => setShowAllBpi(!showAllBpi)}
                className="text-red-600 hover:underline text-sm"
              >
                {showAllBpi ? 'Arată mai puțin' : `Arată toate (${bpiRecords.length})`}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LegalInfo;
