# Dokumentacija za Sustav za Sigurno Dijeljenje Datoteka

## Korišteni programski jezici i tehnologije

### Programski jezici
- **Python**: Glavni backend jezik za serversku logiku i obradu podataka
- **JavaScript (ES6+)**: Frontend React aplikacija, AJAX za API komunikaciju
- **JSX**: React komponente templating
- **HTML**: Struktura web stranica
- **CSS**: Stiliziranje web stranica

### Web tehnologije
- **Flask**: Python web framework za izradu backend API-ja
- **React**: JavaScript biblioteka za izgradnju korisničkih sučelja
- **React Router**: Usmjeravanje i navigacija za React aplikacije
- **Axios**: HTTP klijent za API zahtjeve
- **React Dropzone**: Funkcionalnost povuci-i-ispusti za prijenos datoteka
- **i18next**: Framework za internacionalizaciju u React-u
- **SQLAlchemy**: ORM (Object-Relational Mapping) za rad s bazom podataka
- **Flask-Bcrypt**: Hashiranje i validacija lozinki
- **Flask-Babel**: Podrška za internacionalizaciju i lokalizaciju
- **Bootstrap**: Frontend framework za responzivni dizajn
- **Jest**: JavaScript testing framework za React komponente
- **pytest**: Python testing framework za backend kod
- **CORS Support**: Cross-Origin Resource Sharing za API pristup
- **Docker Compose**: Definicija više-kontejnerskog okruženja
- **GitHub Actions**: CI/CD automatizacija
- **Makefile**: Automatizacija izgradnje i orkestracije testova
- **Cryptography**: Python biblioteka za sigurno šifriranje/dešifriranje

### Baze podataka
- **PostgreSQL**: Primarna baza podataka koja se koristi u svim okruženjima (lokalni Docker, razvoj i produkcija)

### Infrastruktura i deployment
- **Docker**: Kontejnerizacija aplikacije za jednostavno pokretanje i deployment
- **npm**: Upravitelj paketa za JavaScript ovisnosti
- **Heroku**: Cloud platforma za hosting aplikacije (LIVE DEMO: https://uploadfile-47843913ee68.herokuapp.com/)

### Sigurnost i validacija
- **Werkzeug**: Utility biblioteka za sigurnosne funkcije
- **Regularne ekspresije**: Validacija i sanitizacija korisničkog unosa
- **MIME validacija**: Provjera stvarnog tipa uploadanih datoteka
- **Fernet enkripcija**: Simetrično šifriranje za datoteke i osjetljive podatke
- **Generiranje ključeva iz lozinke**: PBKDF2 za sigurno generiranje ključeva

### Praćenje i dijagnostika
- **Python logging**: Strukturirano logiranje aktivnosti
- **RotatingFileHandler**: Rotiranje log datoteka za optimalno korištenje prostora

## Sadržaj

1. [Tehnička dokumentacija](#tehnička-dokumentacija)
   - [Arhitektura sustava](#arhitektura-sustava)
   - [Sigurnosne implementacije](#sigurnosne-implementacije)
   - [Implementacija logiranja](#implementacija-logiranja)
   - [Podrška za višejezičnost](#podrška-za-višejezičnost)
   - [Shema baze podataka](#shema-baze-podataka)
   - [API krajnje točke](#api-krajnje-točke)
   - [Upravljanje pogreškama](#upravljanje-pogreškama)
   - [Tehnički zahtjevi](#tehnički-zahtjevi)
   - [Okvir za testiranje](#okvir-za-testiranje)
   
2. [Korisnička dokumentacija](#korisnička-dokumentacija)
   - [Instalacija i postavljanje](#instalacija-i-postavljanje)
   - [Korištenje aplikacije](#korištenje-aplikacije)
   - [Sigurnosne preporuke](#sigurnosne-preporuke)
   - [Rješavanje problema](#rješavanje-problema)
   - [Frontend arhitektura](#frontend-arhitektura)

## Tehnička dokumentacija

### Arhitektura sustava

Sustav za sigurno dijeljenje datoteka implementiran je kao moderna web aplikacija s React frontend-om i Flask backend API-jem:

- **Backend**: Flask-baziran RESTful API koji upravlja operacijama podataka i datoteka
- **Frontend**: React SPA (Single Page Application) koji pruža responzivno i interaktivno korisničko sučelje
- **Komunikacija**: JSON-bazirana API komunikacija između frontend-a i backend-a

Glavne komponente sustava su:

1. **Backend API**: Flask aplikacija koja upravlja HTTP zahtjevima i API odgovorima
2. **Frontend SPA**: React aplikacija za korisničko sučelje i interakciju
3. **Baza podataka**: PostgreSQL za pohranu metapodataka o uploadanim datotekama
4. **Sustav za datoteke**: Lokalni datotečni sustav za pohranu uploadanih datoteka
5. **Sustav za logiranje**: Strukturirano logiranje aktivnosti korisnika i sustava
6. **Sloj za enkripciju**: Fernet-bazirano šifriranje za datoteke i polja u bazi podataka

Aplikacija implementira slijedeće funkcionalne cjeline:

- Sigurno uploadanje datoteka s podrškom za povuci-i-ispusti
- Sigurno preuzimanje datoteka zaštićeno lozinkom
- Strukturirano logiranje svih aktivnosti
- Pregledavanje logova aktivnosti s tabovima
- Internacionalizacija s promjenom jezika
- End-to-end enkripcija sadržaja datoteka i metapodataka

### Sigurnosne implementacije

#### Validacija i sanitizacija unosa

1. **Validacija vrste datoteke**:
   - Provjera ekstenzije datoteke protiv bijele liste dozvoljenih tipova
   - Dozvoljeni formati: txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx, zip
   - Dodatna provjera MIME tipa datoteke

2. **Validacija veličine datoteke**:
   - Limit veličine datoteke postavljen na 10MB
   - Provjera veličine datoteke korištenjem metoda `seek()` i `tell()`

3. **Sanitizacija imena datoteke**:
   - Korištenje Werkzeug-ove funkcije `secure_filename`
   - Dodatna sanitizacija regularnim izrazima za uklanjanje potencijalno opasnih znakova
   - Prefiks UUID-a za osiguravanje jedinstvenosti datoteka

4. **Validacija sadržaja datoteke**:
   - Provjera prvih 2048 bajtova datoteke za potencijalno opasni sadržaj
   - Detekcija i blokiranje skriptnih tagova

#### Zaštita lozinkom

1. **Hashiranje lozinke**:
   - Korištenje Flask-Bcrypt za sigurno hashiranje lozinke
   - Pohrana hash vrijednosti u bazi podataka

2. **Provjera lozinke kod preuzimanja**:
   - Sigurna provjera hash vrijednosti bez otkrivanja originalne lozinke
   - Zaštita od brute-force napada

#### Sustav enkripcije

1. **Enkripcija datoteka**:
   - Fernet simetrična enkripcija za sve uploadane datoteke
   - Automatsko šifriranje pri uploadu i dešifriranje pri downloadu
   - Sigurno upravljanje ključevima s mehanizmom rezerve

2. **Enkripcija polja u bazi podataka**:
   - Transparentna enkripcija osjetljivih polja (ime datoteke, putanja do datoteke)
   - Šifriranje podataka u mirovanju za zaštitu od krađe baze podataka
   - Automatsko dešifriranje prilikom pristupa poljima

3. **Upravljanje ključevima**:
   - Glavni ključ za šifriranje sigurno pohranjen u varijablama okruženja
   - Rezervno generiranje ključa s jasnim upozorenjima
   - Validacija i korekcija formata ključa

4. **Enkripcija bazirana na lozinki**:
   - PBKDF2 generiranje ključa iz lozinke za operacije zaštićene lozinkom
   - Generiranje i pohrana soli za sigurno generiranje ključa
   - Zaštita od napada pomoću rainbow tablice

#### Dodatne sigurnosne mjere

1. **Jedinstveni identifikatori**:
   - Korištenje UUID-a za identifikaciju datoteka
   - Sprječavanje predvidljivih URL-ova

2. **Čišćenje resursa**:
   - Automatsko brisanje uploadanih datoteka u slučaju greške s bazom podataka
   - Sprječavanje zaostalih datoteka u sustavu

3. **Otpornost na pogreške**:
   - Elegantno upravljanje pogreškama pri šifriranju/dešifriranju
   - Rezervni mehanizmi za osiguravanje dostupnosti sustava
   - Detaljno logiranje pogrešaka za sigurnosni nadzor

### Implementacija logiranja

Sustav za logiranje implementiran je koristeći Python-ov `logging` modul s ciljem detaljnog praćenja aktivnosti, dijagnostike i sigurnosnog nadzora.

#### Struktura logiranja

1. **Višestruki log zapisi**:
   - Opći aplikacijski logovi (`app.log`)
   - Sigurnosni logovi (`security.log`) za osjetljive operacije

2. **Rotacija logova**:
   - Ograničenje veličine log datoteka na 10MB
   - Maksimalno 5 backup datoteka za sprječavanje prekomjernog zauzimanja prostora

3. **Kontekstualne informacije u logovima**:
   - Vremenska oznaka (timestamp)
   - Razina loga (INFO, WARNING, ERROR)
   - IP adresa klijenta
   - User agent klijenta
   - Detaljne poruke o aktivnostima

#### Logirane aktivnosti

1. **Osnovne informacije o zahtjevima**:
   - HTTP metoda
   - Putanja
   - Referrer

2. **Upload aktivnosti**:
   - Pokušaji uploada
   - Neuspjeli uploadi s razlogom
   - Uspješni uploadi s detaljima datoteke

3. **Download aktivnosti**:
   - Pristup stranici za preuzimanje
   - Neuspjeli pokušaji autentikacije
   - Uspješna preuzimanja

4. **Greške sustava**:
   - Greške pri interakciji s bazom podataka
   - Greške pri operacijama s datotečnim sustavom
   - Neočekivane iznimke

5. **Sigurnosni događaji**:
   - Neispravni tipovi datoteka
   - Pokušaji zaobilaženja validacije
   - Neuspjeli pokušaji autentikacije
   - Događaji šifriranja/dešifriranja i povezane pogreške

#### Pregled logova

Implementirana je posebna stranica `/logs` koja omogućava pregled:
- Tablice svih uploadanih datoteka
- Logova uspješnih uploada
- Logova uspješnih downloada

### Podrška za višejezičnost

Aplikacija implementira internacionalizaciju i lokalizaciju koristeći Flask-Babel za pružanje višejezičnog korisničkog sučelja:

#### Podržani jezici
- **Hrvatski (hr)**: Primarni jezik
- **Engleski (en)**: Sekundarni jezik s potpunim prijevodom

#### Detalji implementacije
1. **Integracija Flask-Babel**:
   - Konfiguracija u `babel.cfg` za izvlačenje dijelova teksta za prijevod
   - Detekcija jezika iz postavki preglednika i korisničkog odabira
   - Trajno pamćenje odabranog jezika korištenjem kolačića preglednika

2. **Datoteke prijevoda**:
   - Strukturirane kao `translations/<jezični_kod>/LC_MESSAGES/messages.po` 
   - Kompilirane `.mo` datoteke za učinkovito prevođenje tijekom izvršavanja
   - Potpuna pokrivenost svih korisničkih tekstova

3. **Promjena jezika**:
   - Izbornik za odabir jezika u gornjem desnom kutu svake stranice
   - Trenutna promjena jezika bez ponovnog učitavanja stranice
   - Vizualna indikacija trenutno odabranog jezika

4. **Mehanizam rezervnog jezika**:
   - Vraćanje na zadani jezik (hrvatski) kada prijevod nije dostupan
   - Robusno upravljanje rubnim slučajevima prijevoda

#### Proces prevođenja
1. Izvlačenje tekstova za prijevod pomoću `pybabel extract -F babel.cfg -o messages.pot .`
2. Inicijalizacija datoteke prijevoda pomoću `pybabel init -i messages.pot -d translations -l <jezični_kod>`
3. Ažuriranje datoteke prijevoda pomoću `pybabel update -i messages.pot -d translations`
4. Kompilacija prijevoda pomoću `pybabel compile -d translations`

### Shema baze podataka

Za pohranu metapodataka o datotekama koristi se SQLAlchemy ORM s modelom `UploadedFile`:

| Polje | Tip | Opis |
|-------|-----|------|
| id | String(36) | Primarni ključ, UUID |
| _file_name | Text | Šifrirano originalno ime datoteke |
| _file_path | Text | Šifrirana putanja do datoteke u sustavu |
| password_hash | String(255) | Hash vrijednost lozinke |
| password | String(255) | Lozinka (za demonstraciju) |
| upload_date | DateTime | Datum i vrijeme uploada |
| download_count | Integer | Broj preuzimanja |
| is_encrypted | Boolean | Zastavica koja označava je li datoteka šifrirana |
| encryption_salt | LargeBinary | Sol za šifriranje (ako se koristi) |

### API krajnje točke

#### `/` (GET, POST)
- **GET**: Prikazuje početnu stranicu s formom za upload
- **POST**: Obrađuje upload datoteke
  - Parametri forme:
    - `file`: Datoteka za upload
    - `password`: Lozinka za zaštitu datoteke
  - Akcije:
    - Validacija datoteke
    - Pohrana datoteke
    - Šifriranje datoteke
    - Kreiranje zapisa u bazi podataka
    - Generiranje i vraćanje URL-a za preuzimanje

#### `/get-file/<file_uuid>` (GET, POST)
- **GET**: Prikazuje stranicu za unos lozinke za preuzimanje
- **POST**: Obrađuje zahtjev za preuzimanje
  - Parametri forme:
    - `password`: Lozinka za pristup datoteci
  - Akcije:
    - Validacija lozinke
    - Ažuriranje broja preuzimanja
    - Dešifriranje datoteke
    - Slanje datoteke klijentu

#### `/api/download/<file_uuid>` (GET, OPTIONS)
- **GET**: Direktno preuzimanje datoteke nakon autentikacije
  - Parametri upita:
    - `authenticated`: Zastavica koja označava uspješnu autentikaciju
  - Akcije:
    - Provjera autentikacije
    - Dešifriranje datoteke ako je potrebno
    - Sigurno serviranje datoteke

#### `/api/upload` (GET, POST, OPTIONS)
- **GET**: Vraća informacije o zahtjevima za upload
- **POST**: API krajnja točka za upload datoteke
  - Parametri forme:
    - `file`: Datoteka za upload
    - `password`: Lozinka za zaštitu datoteke
  - Akcije:
    - Validacija datoteke
    - Pohrana datoteke
    - Šifriranje datoteke
    - Kreiranje zapisa u bazi podataka
    - Vraćanje JSON-a s detaljima datoteke i URL-om za preuzimanje

#### `/logs` (GET)
- **GET**: Prikazuje logove aktivnosti
  - Akcije:
    - Dohvaćanje liste datoteka iz baze
    - Čitanje i parsiranje log datoteka
    - Prikaz tablice s podacima i logovima

#### `/api/admin/check-files` (GET)
- **GET**: Admin krajnja točka za provjeru i popravak sinkronizacije datotečnog sustava i baze podataka
  - Potrebna zaglavlja (odaberite jedno):
    - `X-Admin-Key`: Autentifikacijski ključ za administratorski pristup (zadano: "admin-key")
  - Akcije:
    - Provjera siročadskih datoteka (datoteke u direktoriju uploads koje nisu u bazi)
    - Provjera nestalih datoteka (zapisi u bazi za koje datoteke ne postoje na disku)
    - Automatski popravak siročadskih datoteka kreiranjem zapisa u bazi
    - Ažuriranje putanja datoteka u bazi ako su pronađene šifrirane verzije
    - Vraćanje JSON-a s detaljima o siročadskim, nestalim i popravljenim datotekama

#### Promjena jezika

1. U gornjem desnom kutu svake stranice nalaze se dugmad za odabir jezika (HR, EN)
2. Kliknite na željeni jezik kako biste promijenili jezik sučelja
3. Odabrani jezik bit će zapamćen za buduće posjete aplikaciji
4. Svi elementi korisničkog sučelja bit će prikazani na odabranom jeziku

### Upravljanje pogreškama

Aplikacija ima implementirano sveobuhvatno upravljanje greškama:

1. **HTTP greške**:
   - Prilagođene stranice za greške 404 (stranica nije pronađena)
   - Prilagođene stranice za greške 500 (interna greška poslužitelja)

2. **Validacijske greške**:
   - Jasne poruke za neispravne tipove datoteka
   - Poruke za prekoračenje veličine datoteke
   - Poruke za neispravno ime datoteke

3. **Greške autentikacije**:
   - Poruke za neispravnu lozinku
   - Poruke za nedostajuću lozinku

4. **Greške šifriranja**:
   - Elegantno upravljanje neuspjesima šifriranja
   - Povratak na nešifrirano pohranjivanje kada je potrebno
   - Transparentno oporavljanje od pogrešaka tijekom dešifriranja

5. **Greške sustava**:
   - Upravljanje greškama baze podataka
   - Upravljanje greškama datotečnog sustava
   - Logiranje detalja grešaka

#### Greška pri promjeni jezika

- **Problem**: "Jezik se ne mijenja kada kliknem na dugme za odabir jezika."
- **Rješenje**: 
  - Provjerite jesu li kolačići (cookies) omogućeni u vašem pregledniku.
  - Pokušajte očistiti cache i kolačiće preglednika.
  - Osigurajte da se stranica u potpunosti ponovno učitava nakon promjene jezika.

### Tehnički zahtjevi

- Python 3.6+
- Flask
- Flask-SQLAlchemy
- Flask-Bcrypt
- Werkzeug
- Cryptography
- PostgreSQL (primarna baza podataka za sva okruženja)

## Okvir za testiranje

Aplikacija uključuje sveobuhvatan okvir za testiranje koji osigurava pouzdanost, sigurnost i funkcionalnost backend i frontend komponenti.

### Tehnologije za testiranje

- **Backend testiranje**: 
  - pytest: Python framework za testiranje
  - Flask Test Client: Za testiranje Flask ruta i API krajnjih točaka
  - Privremena SQLite baza podataka za izolaciju testova
  
- **Frontend testiranje**:
  - Jest: JavaScript framework za testiranje
  - React Testing Library: Za testiranje React komponenti
  - Mock implementacije za API pozive i internacionalizaciju

- **Integracijsko testiranje**:
  - Docker Compose konfiguracija za testiranje u izoliranim kontejnerima
  - End-to-end test workflow putem GitHub Actions

### Struktura testova

#### Backend testovi

1. **Testovi osnovnih ruta** (`tests/test_basic.py`):
   - Testovi za početnu stranicu
   - Testovi za API rutu logova
   - Testovi za rukovanje 404 pogreškama

2. **Testovi operacija s datotekama** (`tests/test_file_operations.py`):
   - Funkcionalnost uploada datoteka
   - Validacija uploada datoteka bez datoteka
   - Validacija uploada datoteka bez lozinki
   
3. **Testovi enkripcije** (`tests/test_encryption.py`):
   - Šifriranje i dešifriranje polja u bazi podataka
   - Šifriranje i dešifriranje datoteka
   - Enkripcija bazirana na lozinki
   - Upravljanje ključevima i validacija
   
4. **Test fixtures** (`tests/conftest.py`):
   - Postavljanje Flask aplikacije s test konfiguracijom
   - Kreiranje test klijenta
   - Inicijalizacija i čišćenje baze podataka

#### Frontend testovi

1. **Testovi komponenti**:
   - Testovi komponente za upload datoteka
   - Testovi navigacijske komponente
   - Testovi App komponente
   
2. **Mock implementacije**:
   - Mock i18n za testiranje internacionalizacije
   - Mock API fetch pozivi za simuliranje odgovora servera

### Pokretanje testova

Različite naredbe za testiranje dostupne su putem Makefile-a za jednostavnije izvršavanje testova:

1. **Pokretanje svih testova**:
   ```bash
   make test
   ```

2. **Pokretanje samo Flask backend testova**:
   ```bash
   make test-flask
   ```

3. **Pokretanje samo React frontend testova**:
   ```bash
   make test-react
   ```

4. **Pokretanje testova u Docker-u**:
   ```bash
   make test-docker
   ```
   
6. **Pokretanje testova enkripcije**
   ```bash
   python -m pytest tests/test_encryption.py -v
   ```

### Pokrivenost testovima

Testovi pokrivaju nekoliko kritičnih aspekata aplikacije:

1. **Sigurnosni testovi**:
   - Rukovanje i zaštita lozinki
   - Validacija i sanitizacija datoteka
   - Rukovanje pogreškama za nevažeće unose
   - Funkcionalnost enkripcije i dekripcije

2. **Funkcionalni testovi**:
   - Workflow uploada i downloada datoteka
   - Odgovori API krajnjih točaka
   - Renderiranje komponenti i interakcije

3. **Testovi korisničkog sučelja**:
   - Renderiranje komponenti
   - Korisničke interakcije (klik događaji, podnošenje formi)
   - Internacionalizacija

### Dodavanje novih testova

Prilikom proširenja aplikacije novim značajkama, slijedite ove smjernice za dodavanje testova:

1. **Backend testovi**:
   - Dodajte nove test funkcije u odgovarajuću test datoteku ili kreirajte novu test datoteku
   - Koristite postojeće fixtures iz conftest.py
   - Slijedite konvenciju imenovanja `test_<naziv_funkcionalnosti>`

2. **Frontend testovi**:
   - Kreirajte nove test datoteke uz datoteke komponenti
   - Koristite konvenciju imenovanja `<NazivKomponente>.test.js`
   - Koristite React Testing Library-ove utilitije za renderiranje i interakciju

## Korisnička dokumentacija

### Instalacija i postavljanje

#### Preduvjeti
- [Docker](https://docs.docker.com/get-docker/) i [Docker Compose](https://docs.docker.com/compose/install/) instalirani na vašem sustavu
- Git za kloniranje repozitorija

#### Postavljanje s Docker Compose (Preporučeno)

Docker Compose pruža najlakši način za postavljanje i pokretanje cijelog stack-a aplikacije s ispravnom konfiguracijom:

1. **Kloniranje repozitorija**
   ```bash
   git clone <url-repozitorija>
   cd flask_file_upload
   ```

2. **Konfiguracija varijabli okruženja (Opcionalno)**
   
   Projekt uključuje zadanu konfiguraciju u `docker-compose.yml` datoteci, ali možete je prilagoditi stvaranjem `.env` datoteke:
   ```bash
   # Primjer sadržaja .env datoteke
   MASTER_ENCRYPTION_KEY=vaš_sigurni_base64_ključ  # Opcionalno: Za produkcijsko korištenje
   ENABLE_STARTUP_CLEANUP=true                    # Omogući čišćenje pri pokretanju
   CLEANUP_STRATEGY=all                           # Opcije: all, db, files, logs ili kombinacije
   ```

   Dostupne strategije čišćenja:
   - `all`: Očisti sve (bazu podataka, uploadane datoteke i logove)
   - `db`: Očisti samo zapise u bazi podataka
   - `files`: Očisti samo uploadane datoteke
   - `logs`: Očisti samo log datoteke
   - Kombinacije odvojene zarezom: `db,logs` za čišćenje baze podataka i logova
   
3. **Izgradnja i pokretanje aplikacije**
   ```bash
   docker-compose up -d
   ```
   
   Ova naredba će:
   - Izgraditi kontejner aplikacije
   - Postaviti PostgreSQL kontejner baze podataka
   - Konfigurirati mrežu između kontejnera
   - Montirati potrebne volumene
   - Pokrenuti aplikaciju na http://localhost:5001

4. **Provjerite radi li aplikacija**
   
   Otvorite svoj preglednik i navigirajte do:
   ```
   http://localhost:5001
   ```

5. **Pregledavanje logova (Opcionalno)**
   ```bash
   docker-compose logs -f
   ```

6. **Zaustavljanje aplikacije**
   ```bash
   docker-compose down
   ```

#### Čišćenje projekta

Projekt uključuje nekoliko metoda za osiguravanje čistog stanja pri ponovnom pokretanju:

1. **Automatsko čišćenje pri pokretanju**
   
   Prema zadanim postavkama, aplikacija je konfigurirana da očisti zapise u bazi podataka, uploadane datoteke i logove pri svakom ponovnom pokretanju. Ovo ponašanje kontroliraju varijable okruženja u `docker-compose.yml`:
   ```yaml
   ENABLE_STARTUP_CLEANUP=true
   CLEANUP_STRATEGY=all
   ```

2. **Ručno čišćenje korištenjem Make naredbi**
   
   Projekt uključuje nekoliko Make naredbi za upravljanje stanjem aplikacije:
   ```bash
   # Pokretanje aplikacije
   make start
   
   # Zaustavljanje aplikacije
   make stop
   
   # Čišćenje svega i vraćanje na početno stanje
   make clean
   
   # Čišćenje svega i ponovno pokretanje aplikacije
   make clean-restart
   
   # Ponovno pokretanje bez čišćenja (zadržava postojeće podatke)
   make restart
   ```

3. **Korištenje skripte za čišćenje**
   
   Za detaljniju kontrolu, koristite uključenu skriptu za čišćenje:
   ```bash
   # Prikaži pomoć
   ./cleanup.sh
   
   # Očisti sve (bazu podataka, uploadane datoteke, logove)
   ./cleanup.sh --all
   
   # Očisti samo bazu podataka
   ./cleanup.sh --db
   
   # Očisti samo uploadane datoteke
   ./cleanup.sh --files
   
   # Očisti samo log datoteke
   ./cleanup.sh --logs
   
   # Očisti sve i ponovno pokreni
   ./cleanup.sh --restart
   ```

4. **Potpuna obnova sustava**

   Ako trebate potpuno svježi početak bez zadržavanja starih podataka:
   ```bash
   # Potpuna obnova - uklanja sve volumene, ponovno gradi kontejnere, svježi početak
   make full-cleanup
   ```
   
   Ova naredba:
   - Zaustavlja sve kontejnere
   - Uklanja volumen baze podataka
   - Ponovno gradi sve Docker slike bez korištenja kache
   - Pokreće sustav potpuno svježe
   - Osigurava da nigdje ne ostaju stari podaci

5. **Čišćenje zapisa logova za izbrisane datoteke**

   Ako ste izbrisali datoteke, ali ih i dalje vidite na stranici logova, koristite skriptu za čišćenje logova:
   ```bash
   # Korištenje posebne skripte
   ./clean_logs.sh
   
   # Ili korištenjem make naredbe
   make clean-logs
   ```
   
   Ovo će ukloniti zapise u logovima za datoteke koje više ne postoje u uploads direktoriju.

#### Testiranje aplikacije

Aplikacija uključuje automatizirane testove koje možete pokrenuti kako biste provjerili funkcionalnosti:

##### Testiranje s Docker Compose

1. **Pokretanje svih testova u Docker okruženju**
   ```bash
   docker-compose -f docker-compose.test.yml up --build
   ```
   Ovo će izgraditi test kontejner i pokrenuti i backend i frontend testove.

2. **Pokretanje samo backend testova**
   ```bash
   docker-compose exec web python -m pytest tests/
   ```

3. **Pokretanje specifičnih test modula**
   ```bash
   docker-compose exec web python -m pytest tests/test_encryption.py -v
   ```

##### Testiranje bez Docker-a

Ako koristite ručno postavljanje:

1. **Instalacija test ovisnosti**
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Pokretanje svih testova**
   ```bash
   make test
   ```

3. **Pokretanje samo backend testova**
   ```bash
   make test-flask
   ```

4. **Pokretanje samo frontend testova**
   ```bash
   make test-react
   ```

Rezultat testova pokazat će funkcioniraju li sve komponente ispravno. Ako neki testovi ne prođu, poruke o greškama mogu pomoći u identifikaciji problema.

### Korištenje aplikacije

#### Uploadanje datoteke

1. Otvorite početnu stranicu aplikacije (`/`)
2. Kliknite na "Choose file" i odaberite datoteku za upload
   - Podržani formati: txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx, zip
   - Maksimalna veličina: 10MB
3. Unesite lozinku koja će biti potrebna za preuzimanje datoteke
4. Kliknite na "Upload"
5. Nakon uspješnog uploada, dobit ćete jedinstveni URL za pristup datoteci
6. Sve datoteke se automatski šifriraju za dodatnu sigurnost

#### Preuzimanje datoteke

1. Otvorite link za preuzimanje datoteke (`/get-file/<file_uuid>`)
2. Unesite lozinku koja je postavljena prilikom uploada
3. Kliknite na "Download"
4. Datoteka će biti automatski dešifrirana i preuzeta na vaše računalo

#### Pregledavanje logova aktivnosti

1. Otvorite stranicu za pregled logova (`/logs`)
2. Pregledajte tablicu s podacima o uploadanim datotekama
3. Koristite tabove za pregled logova uploada i downloada
4. Koristite polje za pretraživanje za filtriranje logova

### Sigurnosne preporuke

1. **Koristite jake lozinke** za zaštitu vaših datoteka.
2. **Ne dijelite URL za preuzimanje** putem nesigurnih kanala.
3. **Redovito brišite nepotrebne datoteke** iz sustava.
4. **Provjerite datoteke na viruse** prije uploada i nakon downloada.
5. **Postavite siguran glavni ključ za šifriranje** u produkcijskim okruženjima.
6. **Redovito mijenjajte ključeve za šifriranje** za poboljšanu sigurnost.

### Rješavanje problema

#### Greška pri uploadu datoteke

- **Problem**: "An error occurred while saving the file."
- **Rješenje**: 
  - Provjerite ima li aplikacija dovoljna prava za pisanje u direktorij `uploads`.
  - Provjerite je li veličina datoteke ispod 10MB.
  - Provjerite je li tip datoteke dozvoljen.

#### Greška pri preuzimanju datoteke

- **Problem**: "Incorrect password!"
- **Rješenje**: 
  - Provjerite jeste li unijeli točnu lozinku.
  - Pazite na velika/mala slova u lozinki.

#### Greška dešifriranja

- **Problem**: "Error processing file download" ili "Decryption failed"
- **Rješenje**: 
  - Osigurajte da se glavni ključ za šifriranje nije promijenio od kada je datoteka uploadana.
  - Ako ste promijenili ključ za šifriranje, možda ćete morati vratiti prethodni ključ.
  - U nekim slučajevima, ponovno pokretanje aplikacije može riješiti privremene kriptografske probleme.

#### Greška pri pristupu logovima

- **Problem**: "Could not load logs"
- **Rješenje**: 
  - Provjerite postoji li direktorij `logs` i ima li aplikacija dovoljna prava za čitanje i pisanje.
  - Ako je potrebno, ručno kreirajte direktorij `logs` u korijenskom direktoriju aplikacije.

#### Greška "File not found"

- **Problem**: "File not found" pri pokušaju preuzimanja
- **Rješenje**: 
  - Provjerite jeste li unijeli ispravan URL za preuzimanje.
  - Ako je datoteka obrisana, više neće biti dostupna za preuzimanje.

#### Greška pri promjeni jezika

- **Problem**: "Jezik se ne mijenja kada kliknem na dugme za odabir jezika."
- **Rješenje**: 
  - Provjerite jesu li kolačići (cookies) omogućeni u vašem pregledniku.
  - Pokušajte očistiti cache i kolačiće preglednika.
  - Osigurajte da se stranica u potpunosti ponovno učitava nakon promjene jezika.

## Frontend arhitektura

Frontend je izgrađen koristeći React sa sljedećom strukturom komponenti:

### Komponente
- **App**: Glavna aplikacijska komponenta i usmjeravanje
- **Navbar**: Navigacijska traka s odabirom jezika
- **FileUpload**: Funkcionalnost povuci-i-ispusti za prijenos datoteka
- **FileDownload**: Preuzimanje datoteka zaštićeno lozinkom
- **ActivityLog**: Sučelje s tabovima za pregledavanje logova uploada/downloada

### Upravljanje stanjem
- Stanje na razini komponente koristeći React hooks (useState, useEffect)
- Context API za globalno stanje (postavke jezika)

### Internacionalizacija
- i18next integracija za višejezičnu podršku
- Detekcija jezika iz postavki preglednika i kolačića
- Promjena jezika s trajnim odabirom

### API integracija
- Axios za HTTP zahtjeve prema Flask backend-u
- JSON-bazirana razmjena podataka
- Rukovanje podacima forme za prijenos datoteka

### Stiliziranje
- Bootstrap 5 za responzivni layout
- Prilagođeni CSS za temu i stiliziranje komponenti
- Responzivni dizajn za mobilne i desktop prikaze 

## Funkcionalnost čišćenja

Aplikacija uključuje sveobuhvatnu funkcionalnost čišćenja kako bi se osiguralo čisto stanje pri svakoj instalaciji i ponovnom pokretanju:

### Automatsko čišćenje

- **Čišćenje pri pokretanju**: Pri pokretanju aplikacije, sustav može automatski očistiti bazu podataka, mapu za prijenos i logove na temelju varijabli okruženja.
- **Konfiguracija okruženja**:
  - `ENABLE_STARTUP_CLEANUP`: Postavite na `true` za omogućavanje čišćenja pri pokretanju (zadano: `true`)
  - `CLEANUP_STRATEGY`: Postavite na `all`, `files`, `db` ili `logs` za kontrolu što se čisti (zadano: `all`)

### Ručno čišćenje

Dostupno je nekoliko naredbi za čišćenje sustava:

```bash
# Čišćenje zapisa logova za datoteke koje više ne postoje
make clean-logs

# Čišćenje svih učitanih datoteka
make clean-files

# Čišćenje zapisa u bazi podataka
make clean-db

# Čišćenje svega i ponovno pokretanje aplikacije
make clean-restart

# Potpuno čišćenje s resetiranjem volumena i potpunom ponovnom izgradnjom
make full-cleanup
```

### Skripte za čišćenje

- `clean_logs.sh`: Uklanja zapise logova za datoteke koje više ne postoje u direktoriju uploads
- `cleanup.sh`: Glavna skripta za čišćenje s opcijama za ciljano čišćenje:
  ```bash
  ./cleanup.sh --db     # Čišćenje samo baze podataka
  ./cleanup.sh --files  # Čišćenje samo učitanih datoteka
  ./cleanup.sh --logs   # Čišćenje samo logova
  ./cleanup.sh --all    # Čišćenje svega (zadano)
  ./cleanup.sh --full   # Potpuna ponovna izgradnja sustava
  ```

### Potpuna ponovna izgradnja

Za svježi početak s potpuno čistim stanjem:

```bash
make full-cleanup
```

Ova naredba:
1. Zaustavlja sve kontejnere
2. Uklanja volumen baze podataka
3. Ponovno izgrađuje kontejnere iz početnog stanja
4. Pokreće aplikaciju s čistim stanjem 