"""
Admin CAEN Routes - Manage CAEN codes collection
Stats, update Rev.1 descriptions, CRUD, CSV import
"""
from fastapi import APIRouter, Depends, UploadFile, File
from auth import get_current_user
from database import get_local_db
import logging
import csv
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/caen", tags=["admin-caen"])

# ── Rev.1 description mapping (from update_caen_rev1_descriptions.py) ──
REV1_DESCRIPTIONS = {
    "5211": "Comert cu amanuntul in magazine nespecializate, cu vanzare predominanta de produse alimentare, bauturi si tutun",
    "5212": "Comert cu amanuntul in magazine nespecializate, cu vanzare predominanta de produse nealimentare",
    "5221": "Comert cu amanuntul al fructelor si legumelor proaspete",
    "5222": "Comert cu amanuntul al carnii si al produselor din carne",
    "5223": "Comert cu amanuntul al pestelui, crustaceelor si molustelor",
    "5224": "Comert cu amanuntul al painii, produselor de patiserie si produselor zaharoase",
    "5225": "Comert cu amanuntul al bauturilor",
    "5226": "Comert cu amanuntul al produselor din tutun",
    "5227": "Comert cu amanuntul al altor produse alimentare, in magazine specializate",
    "5231": "Comert cu amanuntul al produselor farmaceutice",
    "5232": "Comert cu amanuntul al articolelor medicale si ortopedice",
    "5233": "Comert cu amanuntul al produselor cosmetice si de parfumerie",
    "5241": "Comert cu amanuntul al textilelor",
    "5242": "Comert cu amanuntul al imbracamintei",
    "5243": "Comert cu amanuntul al incaltamintei si articolelor din piele",
    "5244": "Comert cu amanuntul al mobilei, al articolelor de iluminat si al altor articole de uz casnic",
    "5245": "Comert cu amanuntul al articolelor si aparatelor electrocasnice, de radio si de televiziune",
    "5246": "Comert cu amanuntul al articolelor de fierarie, al articolelor din sticla si a celor pentru vopsit",
    "5247": "Comert cu amanuntul al cartilor, ziarelor si articolelor de papetarie",
    "5248": "Comert cu amanuntul, in magazine specializate, al altor produse n.c.a.",
    "5250": "Comert cu amanuntul al bunurilor de ocazie vandute prin magazine",
    "5261": "Comert cu amanuntul prin intermediul caselor de comenzi",
    "5262": "Comert cu amanuntul prin standuri si piete",
    "5263": "Comert cu amanuntul care nu se efectueaza prin magazine",
    "5271": "Repararea incaltamintei si a altor articole din piele",
    "5272": "Repararea aparatelor electrice de uz casnic",
    "5273": "Repararea ceasurilor si bijuteriilor",
    "5274": "Alte reparatii de articole personale si gospodaresti n.c.a.",
    "5111": "Intermedieri in comertul cu materii prime agricole, animale vii, materii prime textile si cu semifabricate",
    "5112": "Intermedieri in comertul cu combustibili, minereuri, metale si produse chimice pentru industrie",
    "5113": "Intermedieri in comertul cu material lemnos si materiale de constructii",
    "5114": "Intermedieri in comertul cu masini, echipamente industriale, nave si avioane",
    "5115": "Intermedieri in comertul cu mobila, articole de menaj si de fierarie",
    "5116": "Intermedieri in comertul cu textile, confectii din blana, incaltaminte si articole din piele",
    "5117": "Intermedieri in comertul cu produse alimentare, bauturi si tutun",
    "5118": "Intermedieri in comertul specializat in vanzarea produselor cu caracter specific n.c.a.",
    "5119": "Intermedieri in comertul cu produse diverse",
    "5121": "Comert cu ridicata al cerealelor, semintelor, furajelor si tutunului neprelucrat",
    "5122": "Comert cu ridicata al florilor si al plantelor",
    "5123": "Comert cu ridicata al animalelor vii",
    "5124": "Comert cu ridicata al blanurilor, pieilor brute si al pieilor prelucrate",
    "5131": "Comert cu ridicata al fructelor si legumelor",
    "5132": "Comert cu ridicata al carnii si produselor din carne",
    "5133": "Comert cu ridicata al produselor lactate, oualor, uleiurilor si grasimilor comestibile",
    "5134": "Comert cu ridicata al bauturilor",
    "5135": "Comert cu ridicata al produselor din tutun",
    "5136": "Comert cu ridicata al zaharului, ciocolatei si produselor zaharoase",
    "5137": "Comert cu ridicata cu cafea, ceai, cacao si condimente",
    "5138": "Comert cu ridicata specializat al altor alimente",
    "5139": "Comert cu ridicata nespecializat de produse alimentare, bauturi si tutun",
    "5141": "Comert cu ridicata al produselor textile",
    "5142": "Comert cu ridicata al imbracamintei si incaltamintei",
    "5143": "Comert cu ridicata al aparatelor electrice de uz gospodaresc, de radio si televiziune",
    "5144": "Comert cu ridicata al produselor din ceramica, sticlarie",
    "5145": "Comert cu ridicata al produselor cosmetice si de parfumerie",
    "5146": "Comert cu ridicata al produselor farmaceutice",
    "5147": "Comert cu ridicata al altor bunuri de consum, nealimentare, n.c.a.",
    "5151": "Comert cu ridicata al combustibililor solizi, lichizi si gazosi si al produselor derivate",
    "5152": "Comert cu ridicata al metalelor si minereurilor metalice",
    "5153": "Comert cu ridicata al materialului lemnos si a materialelor de constructii",
    "5154": "Comert cu ridicata al echipamentelor si furniturilor de fierarie",
    "5155": "Comert cu ridicata al produselor chimice",
    "5156": "Comert cu ridicata al altor produse intermediare",
    "5157": "Comert cu ridicata al deseurilor si resturilor",
    "5181": "Comert cu ridicata al masinilor-unelte",
    "5182": "Comert cu ridicata al masinilor pentru industria miniera si constructii",
    "5183": "Comert cu ridicata al masinilor pentru industria textila",
    "5184": "Comert cu ridicata al calculatoarelor, echipamentelor periferice si software-ului",
    "5185": "Comert cu ridicata al altor masini si echipamente de birou",
    "5186": "Comert cu ridicata de componente si echipamente electronice si de telecomunicatii",
    "5187": "Comert cu ridicata al altor masini si echipamente",
    "5188": "Comert cu ridicata al masinilor agricole",
    "5190": "Comert cu ridicata nespecializat",
    "5010": "Comert cu autovehicule",
    "5020": "Intretinerea si repararea autovehiculelor",
    "5030": "Comert cu piese si accesorii pentru autovehicule",
    "5040": "Comert cu motociclete, piese si accesorii aferente",
    "5050": "Comert cu amanuntul al carburantilor pentru autovehicule",
    "5510": "Hoteluri",
    "5511": "Hoteluri si moteluri cu restaurant",
    "5512": "Hoteluri si moteluri fara restaurant",
    "5521": "Tabere de tineret si refugii",
    "5522": "Campinguri, inclusiv parcaje pentru rulote",
    "5523": "Alte mijloace de cazare",
    "5530": "Restaurante",
    "5540": "Baruri",
    "5541": "Cafenele si baruri fara spectacol",
    "5551": "Cantine",
    "5552": "Alte unitati de preparare a hranei",
    "6010": "Transporturi pe calea ferata",
    "6021": "Transporturi urbane, suburbane si metropolitane de calatori",
    "6022": "Transporturi cu taxiuri",
    "6023": "Alte transporturi terestre de calatori",
    "6024": "Transporturi rutiere de marfuri",
    "6030": "Transporturi prin conducte",
    "6110": "Transporturi maritime si costiere",
    "6120": "Transporturi pe cai navigabile interioare",
    "6210": "Transporturi aeriene dupa orare fixe",
    "6220": "Transporturi aeriene ocazionale",
    "6230": "Transporturi spatiale",
    "6311": "Manipulari",
    "6312": "Depozitari",
    "6321": "Alte activitati anexe transporturilor terestre",
    "6322": "Alte activitati anexe transporturilor pe apa",
    "6323": "Alte activitati anexe transporturilor aeriene",
    "6330": "Activitati ale agentiilor de turism si asistenta turistica n.c.a.",
    "6340": "Activitati ale altor agentii de transport",
    "6411": "Activitati ale postei nationale",
    "6412": "Alte activitati de curier (altele decat cele ale postei nationale)",
    "6420": "Telecomunicatii",
    "6511": "Activitati ale bancii centrale (nationale)",
    "6512": "Alte activitati de intermedieri monetare",
    "6521": "Leasing financiar",
    "6522": "Alte forme de credit",
    "6523": "Alte intermedieri financiare n.c.a.",
    "6601": "Activitati de asigurari de viata",
    "6602": "Activitati ale fondurilor de pensii",
    "6603": "Alte activitati de asigurari (exclusiv asigurarile de viata)",
    "6711": "Activitati de administrare a pietelor financiare",
    "6712": "Activitati de intermediere a tranzactiilor financiare",
    "6713": "Activitati auxiliare intermedierilor financiare n.c.a.",
    "6720": "Activitati auxiliare ale caselor de asigurari si de pensii",
    "7011": "Dezvoltare (promovare) imobiliara",
    "7012": "Cumpararea si vanzarea de bunuri imobiliare proprii",
    "7020": "Inchirierea si subinchirierea bunurilor imobiliare proprii sau inchiriate",
    "7031": "Agentii imobiliare",
    "7032": "Administrarea imobilelor pe baza de comision sau contract",
    "7110": "Inchirierea autoturismelor si a utilitarelor de capacitate mica",
    "7121": "Inchirierea altor mijloace de transport terestru",
    "7122": "Inchirierea mijloacelor de transport pe apa",
    "7123": "Inchirierea mijloacelor de transport aerian",
    "7131": "Inchirierea masinilor si echipamentelor agricole",
    "7132": "Inchirierea masinilor si echipamentelor pentru constructii",
    "7133": "Inchirierea masinilor si echipamentelor de birou, inclusiv calculatoare",
    "7134": "Inchirierea altor masini si echipamente n.c.a.",
    "7140": "Inchirierea bunurilor personale si gospodaresti n.c.a.",
    "7210": "Consultanta in domeniul echipamentelor de calcul (hardware)",
    "7221": "Editare de programe (software)",
    "7222": "Consultanta si furnizare de alte produse software",
    "7230": "Prelucrarea informatica a datelor",
    "7240": "Activitati legate de bazele de date",
    "7250": "Intretinerea si repararea masinilor de birou, de contabilizat si a calculatoarelor",
    "7260": "Alte activitati legate de informatica",
    "7310": "Cercetare-dezvoltare in stiinte fizice si naturale",
    "7320": "Cercetare-dezvoltare in stiinte sociale si umaniste",
    "7411": "Activitati juridice",
    "7412": "Activitati de contabilitate si audit financiar; consultanta in domeniul fiscal",
    "7413": "Activitati de studiere a pietei si de sondare a opiniei publice",
    "7414": "Activitati de consultanta pentru afaceri si management",
    "7415": "Activitati de management al holdingurilor",
    "7420": "Activitati de arhitectura, inginerie si servicii de consultanta tehnica legate de acestea",
    "7430": "Activitati de testare si analize tehnice",
    "7440": "Publicitate",
    "7450": "Selectia si plasarea fortei de munca",
    "7460": "Activitati de investigatii si protectie",
    "7470": "Activitati de curatenie si intretinere",
    "7481": "Activitati fotografice",
    "7482": "Activitati de ambalare",
    "7485": "Activitati de secretariat si traducere",
    "7486": "Activitati ale centrelor de intermediere telefonica (call center)",
    "7487": "Alte activitati de servicii prestate in principal intreprinderilor",
    "7491": "Activitati ale agentiilor de colectare si a birourilor de raportare a creditului",
    "4100": "Captarea, tratarea si distributia apei",
    "4500": "Constructii",
    "4511": "Demolarea constructiilor, terasamente si organizare de santiere",
    "4512": "Lucrari de foraj si sondaj pentru constructii",
    "4521": "Constructii de cladiri si lucrari de geniu civil",
    "4522": "Lucrari de invelitori, sarpante si terase la constructii",
    "4523": "Constructia de autostrazi, drumuri, aerodromuri si baze sportive",
    "4524": "Constructii hidrotehnice",
    "4525": "Alte lucrari speciale de constructii",
    "4531": "Lucrari de instalatii electrice",
    "4532": "Lucrari de izolatii si protectie anticorosiva",
    "4533": "Lucrari de instalatii tehnico-sanitare",
    "4534": "Alte lucrari de instalatii",
    "4541": "Lucrari de ipsoserie",
    "4542": "Lucrari de tamplarie si dulgherie",
    "4543": "Lucrari de pardosire si placare a peretilor",
    "4544": "Lucrari de vopsitorie, zugraveli si montari de geamuri",
    "4545": "Alte lucrari de finisare",
    "1511": "Productia, prelucrarea si conservarea carnii",
    "1512": "Prelucrarea si conservarea pestelui si a produselor din peste",
    "1513": "Prelucrarea si conservarea fructelor si legumelor",
    "1520": "Fabricarea produselor lactate",
    "1531": "Fabricarea produselor de morarit",
    "1532": "Fabricarea amidonului si a produselor din amidon",
    "1533": "Fabricarea produselor pentru hrana animalelor",
    "1541": "Fabricarea produselor de brutarie si patiserie",
    "1542": "Fabricarea biscuitilor si piscoturilor",
    "1543": "Fabricarea zaharului",
    "1544": "Fabricarea macaroanelor, taiteilor si a altor produse fainoase",
    "1551": "Distilarea, rafinarea si mixarea bauturilor alcoolice",
    "1552": "Fabricarea vinurilor din struguri",
    "1553": "Fabricarea berii",
    "1554": "Fabricarea maltului",
    "1555": "Fabricarea bauturilor racoritoare nealcoolice",
    "1560": "Fabricarea produselor din tutun",
    "1571": "Fabricarea produselor pentru hrana animalelor de ferma",
    "1572": "Fabricarea produselor pentru hrana animalelor de companie",
    "1581": "Fabricarea painii si a produselor proaspete de patiserie",
    "1582": "Fabricarea biscuitilor si piscoturilor",
    "1583": "Fabricarea zaharului",
    "1584": "Fabricarea produselor din cacao, a ciocolatei si a produselor zaharoase",
    "1585": "Fabricarea macaroanelor, taiteilor si a altor produse fainoase",
    "1586": "Prelucrarea ceaiului si cafelei",
    "1587": "Fabricarea condimentelor si ingredientelor",
    "1588": "Fabricarea preparatelor alimentare omogenizate si alimentelor dietetice",
    "1589": "Fabricarea altor produse alimentare n.c.a.",
    "1591": "Distilarea, rafinarea si mixarea bauturilor alcoolice",
    "1592": "Fabricarea alcoolului etilic de fermentatie",
    "1593": "Fabricarea vinurilor din struguri",
    "1594": "Fabricarea cidrului si a altor vinuri din fructe",
    "1595": "Fabricarea altor bauturi nedistilate, obtinute prin fermentare",
    "1596": "Fabricarea berii",
    "1597": "Fabricarea maltului",
    "1598": "Productia de bauturi racoritoare nealcoolice; productia de ape minerale",
    "1600": "Fabricarea produselor din tutun",
    "1711": "Pregatirea fibrelor si filarea fibrelor de bumbac si tip bumbac",
    "1712": "Pregatirea fibrelor si filarea fibrelor de lana cardata si tip lana cardata",
    "1713": "Pregatirea fibrelor si filarea fibrelor de lana pieptanata si tip lana pieptanata",
    "1714": "Pregatirea fibrelor si filarea fibrelor tip in",
    "1715": "Rasucirea si pregatirea matasii; rasucirea si texturarea firelor sintetice si artificiale",
    "1716": "Fabricarea atei de cusut",
    "1717": "Pregatirea fibrelor si filarea altor fibre textile",
    "1721": "Productia de tesaturi din bumbac si tip bumbac",
    "1722": "Productia de tesaturi din lana cardata si tip lana cardata",
    "1723": "Productia de tesaturi din lana pieptanata si tip lana pieptanata",
    "1724": "Productia de tesaturi din matase si tip matase",
    "1725": "Productia altor tesaturi",
    "1810": "Fabricarea articolelor de imbracaminte din piele",
    "1821": "Fabricarea articolelor de imbracaminte pentru lucru",
    "1822": "Fabricarea altor articole de imbracaminte (exclusiv lenjeria de corp)",
    "1823": "Fabricarea articolelor de lenjerie de corp",
    "1824": "Fabricarea altor articole de imbracaminte si accesorii n.c.a.",
    "1830": "Prepararea si vopsirea blanurilor; fabricarea articolelor din blana",
    "2010": "Taierea si rindeluirea lemnului; impregnarea lemnului",
    "2020": "Fabricarea de produse stratificate din lemn",
    "2030": "Fabricarea de elemente de dulgherie si tamplarie pentru constructii",
    "2040": "Fabricarea ambalajelor din lemn",
    "2051": "Fabricarea altor produse din lemn",
    "2052": "Fabricarea articolelor din pluta, paie si din alte materiale vegetale impletite",
    "2111": "Fabricarea celulozei",
    "2112": "Fabricarea hartiei si cartonului",
    "2121": "Fabricarea hartiei si cartonului ondulat si a ambalajelor din hartie si carton",
    "2122": "Fabricarea produselor de uz gospodaresc din hartie sau carton",
    "2123": "Fabricarea articolelor de papetarie",
    "2124": "Fabricarea tapetelor",
    "2125": "Fabricarea altor articole din hartie si carton n.c.a.",
    "2211": "Editarea cartilor",
    "2212": "Editarea ziarelor",
    "2213": "Editarea revistelor si periodicelor",
    "2214": "Editarea inregistrarilor sonore",
    "2215": "Alte activitati de editare",
    "2221": "Tiparirea ziarelor",
    "2222": "Alte activitati de tiparire n.c.a.",
    "2223": "Legatorie si finisare",
    "2224": "Compositie si fotogravura",
    "2225": "Alte lucrari de tipar",
    "2231": "Reproducerea inregistrarilor audio",
    "2232": "Reproducerea inregistrarilor video",
    "2233": "Reproducerea inregistrarilor informatice",
    "8010": "Invatamant primar si prescolar",
    "8021": "Invatamant secundar general",
    "8022": "Invatamant secundar, tehnic sau profesional",
    "8030": "Invatamant superior",
    "8041": "Scoli de conducere (pilotaj)",
    "8042": "Alte forme de invatamant",
    "8511": "Activitati de asistenta spitaliceasca",
    "8512": "Activitati de asistenta medicala ambulatorie",
    "8513": "Activitati de asistenta stomatologica",
    "8514": "Alte activitati referitoare la sanatatea umana",
    "8520": "Activitati veterinare",
    "8531": "Activitati de asistenta sociala, cu cazare",
    "8532": "Activitati de asistenta sociala, fara cazare",
    "9001": "Colectarea si tratarea apelor uzate",
    "9002": "Colectarea si tratarea altor reziduuri",
    "9003": "Salubritate, depoluare si activitati similare",
    "9111": "Activitati ale organizatiilor economice si patronale",
    "9112": "Activitati ale organizatiilor profesionale",
    "9120": "Activitati ale sindicatelor salariatilor",
    "9131": "Activitati ale organizatiilor religioase",
    "9132": "Activitati ale organizatiilor politice",
    "9133": "Activitati ale altor organizatii n.c.a.",
    "9211": "Productia de filme cinematografice si video",
    "9212": "Distributia de filme cinematografice si video",
    "9213": "Proiectia de filme cinematografice",
    "9220": "Activitati de radio si televiziune",
    "9231": "Activitati de interpretare artistica (spectacole)",
    "9232": "Activitati auxiliare spectacolelor",
    "9233": "Balciuri si parcuri de distractii",
    "9234": "Alte activitati de spectacole n.c.a.",
    "9240": "Activitati ale agentiilor de presa",
    "9251": "Activitati ale bibliotecilor si arhivelor",
    "9252": "Activitati ale muzeelor, conservarea monumentelor si cladirilor istorice",
    "9253": "Activitati ale gradinilor botanice, zoologice si ale rezervatiilor naturale",
    "9261": "Activitati ale bazelor sportive",
    "9262": "Alte activitati sportive",
    "9271": "Jocuri de noroc si pariuri",
    "9272": "Alte activitati recreative",
    "9301": "Spalarea si curatarea (uscata) articolelor textile si a produselor din blana",
    "9302": "Coafura si alte activitati de infrumusetare",
    "9303": "Activitati de pompe funebre si similare",
    "9304": "Activitati de intretinere corporala",
    "9305": "Alte activitati de servicii n.c.a.",
    "9500": "Activitati ale gospodariilor private in calitate de angajator de personal casnic",
    "9600": "Activitati ale gospodariilor private de producere de bunuri destinate consumului propriu",
    "9700": "Activitati ale gospodariilor private de producere de servicii pentru scopuri proprii",
    "9900": "Activitati ale organizatiilor si organismelor extrateritoriale",
    "7511": "Activitati de administratie publica generala",
    "7512": "Administrarea activitatii organismelor care presteaza servicii in domeniul sanatatii, educatiei, culturii",
    "7513": "Reglementarea si eficientizarea activitatilor economice",
    "7514": "Alte activitati auxiliare pentru guvern",
    "7521": "Activitati de afaceri externe",
    "7522": "Activitati de aparare nationala",
    "7523": "Activitati de justitie",
    "7524": "Activitati de ordine publica si de protectie civila",
    "7525": "Activitati de lupta impotriva incendiilor si de prevenire a acestora",
    "7530": "Activitati de protectie sociala obligatorie",
    "1010": "Extractia si prepararea carbunelui (exclusiv turbei)",
    "1020": "Extractia si prepararea lignitului",
    "1030": "Extractia si prepararea turbei",
    "1110": "Extractia petrolului brut si a gazelor naturale",
    "1120": "Activitati de servicii anexe extractiei petrolului si gazelor naturale",
    "1200": "Extractia minereurilor de uraniu",
    "1310": "Extractia minereurilor metalice feroase",
    "1320": "Extractia minereurilor metalice neferoase (exclusiv uraniu si toriu)",
    "1411": "Extractia pietrei",
    "1412": "Extractia pietrisului si nisipului; extractia argilei si caolinului",
    "1421": "Extractia mineralelor pentru industria chimica si a ingrasamintelor naturale",
    "1422": "Extractia sarii",
    "1430": "Extractia pietrei pentru constructii",
    "1440": "Extractia si prepararea minereurilor radioactive",
    "1450": "Alte activitati extractive n.c.a.",
    "2310": "Fabricarea cocsului",
    "2320": "Fabricarea produselor obtinute din prelucrarea titeiului",
    "2330": "Prelucrarea combustibililor nucleari",
    "2411": "Fabricarea gazelor industriale",
    "2412": "Fabricarea colorantilor si a pigmentilor",
    "2413": "Fabricarea altor produse chimice anorganice, de baza",
    "2414": "Fabricarea altor produse chimice organice, de baza",
    "2415": "Fabricarea ingrasamintelor si produselor azotoase",
    "2416": "Fabricarea materialelor plastice in forme primare",
    "2417": "Fabricarea cauciucului sintetic in forme primare",
    "2420": "Fabricarea pesticidelor si a altor produse agrochimice",
    "2430": "Fabricarea vopselelor, lacurilor, cernelii tipografice si masticurilor",
    "2441": "Fabricarea produselor farmaceutice de baza",
    "2442": "Fabricarea preparatelor farmaceutice",
    "2451": "Fabricarea sapunurilor, detergentilor si a produselor de intretinere",
    "2452": "Fabricarea parfumurilor si a produselor cosmetice",
    "2461": "Fabricarea explozivilor",
    "2462": "Fabricarea cleiurilor si gelatinelor",
    "2463": "Fabricarea uleiurilor esentiale",
    "2464": "Fabricarea preparatelor chimice de uz fotografic",
    "2466": "Fabricarea altor produse chimice n.c.a.",
    "2470": "Fabricarea fibrelor sintetice si artificiale",
    "2511": "Fabricarea anvelopelor si a camerelor de aer",
    "2512": "Resaparea anvelopelor",
    "2513": "Fabricarea altor produse din cauciuc",
    "2521": "Fabricarea placilor, foliilor, tuburilor si profilelor din material plastic",
    "2522": "Fabricarea articolelor de ambalaj din material plastic",
    "2523": "Fabricarea articolelor din material plastic pentru constructii",
    "2524": "Fabricarea altor produse din material plastic",
    "2611": "Fabricarea sticlei plate",
    "2612": "Prelucrarea si fasonarea sticlei plate",
    "2613": "Fabricarea articolelor din sticla",
    "2614": "Fabricarea fibrelor din sticla",
    "2615": "Fabricarea de sticlarie tehnica",
    "2621": "Fabricarea articolelor ceramice pentru uz gospodaresc si ornamental",
    "2622": "Fabricarea de obiecte sanitare din ceramica",
    "2623": "Fabricarea izolatorilor si a pieselor izolante din ceramica",
    "2624": "Fabricarea altor produse ceramice de uz tehnic",
    "2625": "Fabricarea altor produse ceramice",
    "2626": "Fabricarea produselor ceramice refractare",
    "2630": "Fabricarea placilor si dalelor din ceramica",
    "2640": "Fabricarea caramizilor, tiglelor si a altor produse pentru constructii",
    "2651": "Fabricarea cimentului",
    "2652": "Fabricarea varului",
    "2653": "Fabricarea ipsosului",
    "2661": "Fabricarea elementelor din beton pentru constructii",
    "2662": "Fabricarea elementelor din ipsos pentru constructii",
    "2663": "Fabricarea betonului",
    "2664": "Fabricarea mortarului",
    "2665": "Fabricarea produselor din azbociment",
    "2666": "Fabricarea altor elemente din beton, ciment si ipsos",
    "2670": "Taierea, fasonarea si finisarea pietrei",
    "2681": "Fabricarea de produse abrazive",
    "2682": "Fabricarea altor produse din minerale nemetalice n.c.a.",
    "2710": "Productia de metale feroase sub forme primare si de feroaliaje",
    "2721": "Productia de tuburi din fonta",
    "2722": "Productia de tuburi din otel",
    "2731": "Tragere la rece",
    "2732": "Laminare la rece a benzilor inguste",
    "2733": "Productia de profile obtinute la rece",
    "2734": "Trefilarea firelor",
    "2741": "Productia metalelor pretioase",
    "2742": "Productia aluminiului",
    "2743": "Productia plumbului, zincului si cositorului",
    "2744": "Productia cuprului",
    "2745": "Productia altor metale neferoase",
    "2751": "Turnarea fontei",
    "2752": "Turnarea otelului",
    "2753": "Turnarea metalelor neferoase usoare",
    "2754": "Turnarea altor metale neferoase",
    "2811": "Fabricarea de constructii metalice",
    "2812": "Fabricarea de elemente de dulgherie si tamplarie din metal",
    "2821": "Productia de rezervoare, cisterne si containere metalice",
    "2822": "Productia de radiatoare si cazane pentru incalzire centrala",
    "2830": "Productia generatoarelor de abur",
    "2840": "Fabricarea produselor metalice obtinute prin deformare plastica",
    "2851": "Tratarea si acoperirea metalelor",
    "2852": "Operatiuni de mecanica generala",
    "2861": "Fabricarea produselor de taiat",
    "2862": "Fabricarea uneltelor",
    "2863": "Fabricarea articolelor de feronerie",
    "2871": "Fabricarea de recipienti si containere metalice",
    "2872": "Fabricarea ambalajelor metalice usoare",
    "2873": "Fabricarea articolelor din fire metalice",
    "2874": "Fabricarea de suruburi, buloane, lanturi si arcuri",
    "2875": "Fabricarea altor produse metalice n.c.a.",
    "2911": "Fabricarea de motoare si turbine",
    "2912": "Fabricarea de pompe si compresoare",
    "2913": "Fabricarea de articole de robinetarie",
    "2914": "Fabricarea lagarelor, angrenajelor si organelor mecanice de transmisie",
    "2921": "Fabricarea cuptoarelor industriale",
    "2922": "Fabricarea echipamentelor de ridicat si manipulat",
    "2923": "Fabricarea echipamentelor de ventilatie si frigorifice",
    "2924": "Fabricarea altor echipamente de utilizare generala",
    "2931": "Fabricarea tractoarelor",
    "2932": "Fabricarea altor masini si utilaje pentru agricultura si exploatari forestiere",
    "2941": "Fabricarea masinilor-unelte portabile actionate electric",
    "2942": "Fabricarea altor masini-unelte pentru prelucrarea metalului",
    "2943": "Fabricarea altor masini-unelte n.c.a.",
    "2951": "Fabricarea utilajelor pentru metalurgie",
    "2952": "Fabricarea utilajelor pentru extractie si constructii",
    "2953": "Fabricarea utilajelor pentru industria alimentara",
    "2954": "Fabricarea utilajelor pentru industria textila",
    "2955": "Fabricarea utilajelor pentru industria hartiei si cartonului",
    "2956": "Fabricarea altor masini si utilaje specifice n.c.a.",
    "2960": "Fabricarea armamentului si munitiei",
    "2971": "Fabricarea de aparate electrocasnice",
    "2972": "Fabricarea de aparate neelectrice de uz casnic",
    "3001": "Fabricarea masinilor de birou",
    "3002": "Fabricarea calculatoarelor si a altor echipamente electronice",
    "3110": "Fabricarea motoarelor, generatoarelor si transformatoarelor electrice",
    "3120": "Fabricarea aparatelor de distributie si control al electricitatii",
    "3130": "Fabricarea de fire si cabluri izolate",
    "3140": "Fabricarea acumulatorilor si bateriilor",
    "3150": "Fabricarea de corpuri de iluminat si becuri electrice",
    "3161": "Fabricarea echipamentelor electrice pentru motoare si vehicule n.c.a.",
    "3162": "Fabricarea altor echipamente electrice n.c.a.",
    "3210": "Fabricarea de componente electronice",
    "3220": "Fabricarea de echipamente de emisie si transmisie",
    "3230": "Fabricarea de aparate de receptie, inregistrare si reproducere audio si video",
    "3310": "Fabricarea de aparatura medicala si chirurgicala si de dispozitive ortopedice",
    "3320": "Fabricarea de instrumente si dispozitive pentru masura, verificare, control",
    "3330": "Fabricarea echipamentelor de automatizare a proceselor industriale",
    "3340": "Fabricarea de instrumente optice si echipamente fotografice",
    "3350": "Fabricarea de ceasuri",
    "3410": "Productia de autovehicule",
    "3420": "Productia de caroserii, remorci si semiremorci",
    "3430": "Productia de piese si accesorii pentru autovehicule si pentru motoare",
    "3511": "Constructia si repararea de nave maritime si fluviale",
    "3512": "Constructia si repararea de ambarcatiuni sportive si de agrement",
    "3520": "Constructia si repararea materialului rulant",
    "3530": "Constructia de aeronave si de vehicule spatiale",
    "3541": "Fabricarea de motociclete",
    "3542": "Fabricarea de biciclete",
    "3543": "Fabricarea de vehicule pentru invalizi",
    "3550": "Fabricarea altor mijloace de transport n.c.a.",
    "3611": "Fabricarea de scaune",
    "3612": "Fabricarea de mobila pentru birouri si magazine",
    "3613": "Fabricarea de mobila pentru bucatarii",
    "3614": "Fabricarea altor tipuri de mobila",
    "3615": "Fabricarea de saltele si somiere",
    "3621": "Fabricarea monedelor",
    "3622": "Fabricarea bijuteriilor si articolelor similare din metale pretioase",
    "3630": "Fabricarea instrumentelor muzicale",
    "3640": "Fabricarea articolelor pentru sport",
    "3650": "Fabricarea jocurilor si jucariilor",
    "3661": "Fabricarea bijuteriilor de fantazie",
    "3662": "Fabricarea maturilor si periilor",
    "3663": "Fabricarea altor produse manufacturiere n.c.a.",
    "3710": "Recuperarea deseurilor si resturilor metalice reciclabile",
    "3720": "Recuperarea deseurilor si resturilor nemetalice reciclabile",
    "4010": "Productia si distributia de energie electrica",
    "4020": "Productia si distributia gazelor",
    "4030": "Productia si distributia energiei termice, apei calde si aburului",
    "4933": "Alte transporturi terestre de calatori pe baza de grafic",
    "9999": "Activitate nespecificata / Cod CAEN nedefinit",
}


def _determine_section(code: str) -> str:
    """Determine CAEN section letter from code prefix."""
    try:
        d = int(code[:2])
    except (ValueError, TypeError):
        return ""
    if 1 <= d <= 3: return "A"
    elif 5 <= d <= 9: return "B"
    elif 10 <= d <= 33: return "C"
    elif d == 35: return "D"
    elif 36 <= d <= 39: return "E"
    elif 41 <= d <= 43: return "F"
    elif 45 <= d <= 47: return "G"
    elif 49 <= d <= 53: return "H"
    elif 55 <= d <= 56: return "I"
    elif 58 <= d <= 63: return "J"
    elif 64 <= d <= 66: return "K"
    elif d == 68: return "L"
    elif 69 <= d <= 75: return "M"
    elif 77 <= d <= 82: return "N"
    elif d == 84: return "O"
    elif d == 85: return "P"
    elif 86 <= d <= 88: return "Q"
    elif 90 <= d <= 93: return "R"
    elif 94 <= d <= 96: return "S"
    elif 97 <= d <= 98: return "T"
    elif d == 99: return "U"
    return ""


@router.get("/stats")
async def get_caen_stats(current_user=Depends(get_current_user)):
    """Get CAEN codes collection statistics."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    db = get_local_db()
    total = await db.caen_codes.count_documents({})
    generic = await db.caen_codes.count_documents({"name": {"$regex": r"^Cod CAEN \d"}})
    valid = total - generic

    # Count by section
    pipeline = [
        {"$match": {"sectiune": {"$exists": True, "$ne": None, "$ne": ""}}},
        {"$group": {"_id": "$sectiune", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    sections = []
    async for doc in db.caen_codes.aggregate(pipeline):
        sections.append({"sectiune": doc["_id"], "count": doc["count"]})

    # Count codes used by firms (use cached CAEN counts for speed)
    from routes.caen_routes import _get_caen_counts
    try:
        counts = await _get_caen_counts(db)
        used_by_firms = len(counts)
    except Exception:
        used_by_firms = 0

    # Rev.1 codes available in mapping
    rev1_available = len(REV1_DESCRIPTIONS)

    return {
        "total": total,
        "valid_descriptions": valid,
        "generic_descriptions": generic,
        "sections": sections,
        "used_by_firms": used_by_firms,
        "rev1_mapping_size": rev1_available,
    }


@router.post("/update-rev1")
async def update_rev1_descriptions(current_user=Depends(get_current_user)):
    """Update CAEN Rev.1 codes with proper Romanian descriptions."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    db = get_local_db()
    updated = 0
    upserted = 0

    for code, description in REV1_DESCRIPTIONS.items():
        result = await db.caen_codes.update_one(
            {"cod": code, "$or": [
                {"name": {"$regex": "^Cod CAEN "}},
                {"name": {"$exists": False}},
                {"name": ""},
            ]},
            {"$set": {
                "name": description,
                "description": description,
                "denumire": description,
            }},
        )
        if result.modified_count > 0:
            updated += 1

    # Upsert codes that don't exist at all
    for code, description in REV1_DESCRIPTIONS.items():
        existing = await db.caen_codes.find_one({"cod": code})
        if not existing:
            section_letter = _determine_section(code)
            await db.caen_codes.insert_one({
                "cod": code,
                "name": description,
                "description": description,
                "denumire": description,
                "section": code[:2],
                "sectiune": section_letter,
            })
            upserted += 1

    final_count = await db.caen_codes.count_documents({})
    generic_count = await db.caen_codes.count_documents({"name": {"$regex": r"^Cod CAEN \d"}})

    return {
        "updated": updated,
        "upserted": upserted,
        "total": final_count,
        "remaining_generic": generic_count,
    }


@router.get("/codes")
async def list_caen_codes_admin(
    skip: int = 0,
    limit: int = 50,
    q: str = "",
    filter: str = "all",
    current_user=Depends(get_current_user),
):
    """List CAEN codes with pagination, search, and filter."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    db = get_local_db()
    query = {}

    if q.strip():
        query["$or"] = [
            {"cod": {"$regex": q.strip(), "$options": "i"}},
            {"name": {"$regex": q.strip(), "$options": "i"}},
            {"denumire": {"$regex": q.strip(), "$options": "i"}},
        ]

    if filter == "generic":
        query["name"] = {"$regex": r"^Cod CAEN \d"}
    elif filter == "valid":
        query["name"] = {"$not": {"$regex": r"^Cod CAEN \d"}}

    total = await db.caen_codes.count_documents(query)
    cursor = db.caen_codes.find(query, {"_id": 0}).sort("cod", 1).skip(skip).limit(limit)
    codes = await cursor.to_list(limit)

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "codes": codes,
    }


@router.post("/codes")
async def add_caen_code(body: dict, current_user=Depends(get_current_user)):
    """Add a new CAEN code manually."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    cod = body.get("cod", "").strip()
    name = body.get("name", "").strip()
    if not cod or not name:
        return {"error": "cod si name sunt obligatorii"}

    db = get_local_db()
    existing = await db.caen_codes.find_one({"cod": cod})
    if existing:
        return {"error": f"Codul CAEN {cod} exista deja"}

    section_letter = _determine_section(cod)
    doc = {
        "cod": cod,
        "name": name,
        "description": name,
        "denumire": name,
        "section": cod[:2] if len(cod) >= 2 else cod,
        "sectiune": body.get("sectiune", section_letter),
    }
    await db.caen_codes.insert_one(doc)

    return {"status": "created", "cod": cod, "name": name}


@router.put("/codes/{cod}")
async def update_caen_code(cod: str, body: dict, current_user=Depends(get_current_user)):
    """Update a CAEN code's description."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    db = get_local_db()
    update_fields = {}
    if "name" in body:
        name = body["name"].strip()
        update_fields["name"] = name
        update_fields["description"] = name
        update_fields["denumire"] = name
    if "sectiune" in body:
        update_fields["sectiune"] = body["sectiune"].strip()

    if not update_fields:
        return {"error": "Nimic de actualizat"}

    result = await db.caen_codes.update_one({"cod": cod}, {"$set": update_fields})
    if result.matched_count == 0:
        return {"error": f"Codul CAEN {cod} nu a fost gasit"}

    return {"status": "updated", "cod": cod, "modified": result.modified_count}


@router.delete("/codes/{cod}")
async def delete_caen_code(cod: str, current_user=Depends(get_current_user)):
    """Delete a CAEN code."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    db = get_local_db()
    result = await db.caen_codes.delete_one({"cod": cod})
    if result.deleted_count == 0:
        return {"error": f"Codul CAEN {cod} nu a fost gasit"}

    return {"status": "deleted", "cod": cod}


@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    """Import CAEN codes from CSV. Expected columns: cod, name (optional: sectiune)."""
    if current_user.get("role") != "admin":
        return {"error": "Admin only"}

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    # Auto-detect delimiter
    first_line = text.split("\n")[0] if text else ""
    if ";" in first_line:
        delimiter = ";"
    elif "\t" in first_line:
        delimiter = "\t"
    else:
        delimiter = ","
    
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    db = get_local_db()
    imported = 0
    updated = 0
    errors = []

    for i, row in enumerate(reader):
        cod = (row.get("cod") or row.get("code") or row.get("Cod") or "").strip()
        name = (row.get("name") or row.get("denumire") or row.get("Name") or row.get("Denumire") or "").strip()

        if not cod:
            errors.append(f"Rand {i+2}: cod lipsa")
            continue
        if not name:
            errors.append(f"Rand {i+2}: name lipsa pentru cod {cod}")
            continue

        sectiune = (row.get("sectiune") or row.get("section") or "").strip()
        if not sectiune:
            sectiune = _determine_section(cod)

        existing = await db.caen_codes.find_one({"cod": cod})
        if existing:
            await db.caen_codes.update_one(
                {"cod": cod},
                {"$set": {"name": name, "description": name, "denumire": name, "sectiune": sectiune}},
            )
            updated += 1
        else:
            await db.caen_codes.insert_one({
                "cod": cod,
                "name": name,
                "description": name,
                "denumire": name,
                "section": cod[:2] if len(cod) >= 2 else cod,
                "sectiune": sectiune,
            })
            imported += 1

    total = await db.caen_codes.count_documents({})

    return {
        "imported": imported,
        "updated": updated,
        "errors": errors[:20],
        "total_errors": len(errors),
        "total_codes": total,
    }
