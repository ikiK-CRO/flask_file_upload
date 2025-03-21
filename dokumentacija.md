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

### Praćenje i dijagnostika
- **Python logging**: Strukturirano logiranje aktivnosti
- **RotatingFileHandler**: Rotiranje log datoteka za optimalno korištenje prostora

## Sadržaj

1. [Tehnička dokumentacija](#tehnička-dokumentacija)
   - [Arhitektura sustava](#arhitektura-sustava)
   - [Sigurnosne implementacije](#sigurnosne-implementacije)
   - [Implementacija logiranja](#implementacija-logiranja)
   - [Shema baze podataka](#shema-baze-podataka)
   - [API krajnje točke](#api-krajnje-točke)
   - [Upravljanje pogreškama](#upravljanje-pogreškama)
   - [Tehnički zahtjevi](#tehnički-zahtjevi)
   
2. [Korisnička dokumentacija](#korisnička-dokumentacija)
   - [Instalacija i postavljanje](#instalacija-i-postavljanje)
   - [Korištenje aplikacije](#korištenje-aplikacije)
   - [Sigurnosne preporuke](#sigurnosne-preporuke)
   - [Rješavanje problema](#rješavanje-problema)

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

Aplikacija implementira slijedeće funkcionalne cjeline:

- Sigurno uploadanje datoteka s podrškom za povuci-i-ispusti
- Sigurno preuzimanje datoteka zaštićeno lozinkom
- Strukturirano logiranje svih aktivnosti
- Pregledavanje logova aktivnosti s tabovima
- Internacionalizacija s promjenom jezika

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

#### Dodatne sigurnosne mjere

1. **Jedinstveni identifikatori**:
   - Korištenje UUID-a za identifikaciju datoteka
   - Sprječavanje predvidljivih URL-ova

2. **Čišćenje resursa**:
   - Automatsko brisanje uploadanih datoteka u slučaju greške s bazom podataka
   - Sprječavanje zaostalih datoteka u sustavu

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
| file_name | String(255) | Originalno ime datoteke |
| file_path | String(255) | Putanja do datoteke u sustavu |
| password_hash | String(255) | Hash vrijednost lozinke |
| password | String(255) | Lozinka (za demonstraciju) |
| upload_date | DateTime | Datum i vrijeme uploada |
| download_count | Integer | Broj preuzimanja |

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
    - Slanje datoteke klijentu

#### `/logs` (GET)
- **GET**: Prikazuje logove aktivnosti
  - Akcije:
    - Dohvaćanje liste datoteka iz baze
    - Čitanje i parsiranje log datoteka
    - Prikaz tablice s podacima i logovima

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

4. **Greške sustava**:
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
- SQLite (za demonstraciju) ili PostgreSQL (za produkciju)

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
   
3. **Test fixtures** (`tests/conftest.py`):
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

5. **Čišćenje test okruženja**:
   ```bash
   make clean
   ```

### Pokrivenost testovima

Testovi pokrivaju nekoliko kritičnih aspekata aplikacije:

1. **Sigurnosni testovi**:
   - Rukovanje i zaštita lozinki
   - Validacija i sanitizacija datoteka
   - Rukovanje pogreškama za nevažeće unose

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
- Python 3.6 ili noviji
- pip (Python package manager)

#### Koraci za instalaciju

1. **Kloniranje repozitorija**
   ```bash
   git clone <url-repozitorija>
   cd flask_file_upload
   ```

2. **Instalacija potrebnih paketa**
   ```bash
   pip install -r requirements.txt
   ```

3. **Konfiguracija okruženja**
   ```bash
   # Opcijski: Postavite varijable okruženja
   export FLASK_ENV=development # za razvoj
   # ili
   export FLASK_ENV=production # za produkciju
   
   # Za korištenje PostgreSQL baze
   export DATABASE_URL=postgresql://korisnik:lozinka@localhost/baza_podataka
   ```

4. **Pokretanje aplikacije**
   ```bash
   python app.py
   ```
   Aplikacija će biti dostupna na `http://localhost:5000`

#### Docker instalacija

1. **Izgradnja Docker slike**
   ```bash
   docker build -t flask_file_upload .
   ```

2. **Pokretanje Docker kontejnera**
   ```bash
   docker run -p 5000:5000 flask_file_upload
   ```

#### Testiranje aplikacije

Da biste osigurali da aplikacija radi ispravno, možete pokrenuti automatizirane testove:

1. **Instalacija ovisnosti za testiranje**
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

5. **Pokretanje testova u Docker okruženju**
   ```bash
   make test-docker
   ```

Izlaz testova pokazat će vam rade li sve komponente ispravno. Ako neki test ne uspije, poruke o pogreškama pomoći će vam identificirati problem.

### Korištenje aplikacije

#### Uploadanje datoteke

1. Otvorite početnu stranicu aplikacije (`/`)
2. Kliknite na "Choose file" i odaberite datoteku za upload
   - Podržani formati: txt, pdf, png, jpg, jpeg, gif, doc, docx, xls, xlsx, zip
   - Maksimalna veličina: 10MB
3. Unesite lozinku koja će biti potrebna za preuzimanje datoteke
4. Kliknite na "Upload"
5. Nakon uspješnog uploada, dobit ćete jedinstveni URL za pristup datoteci

#### Preuzimanje datoteke

1. Otvorite link za preuzimanje datoteke (`/get-file/<file_uuid>`)
2. Unesite lozinku koja je postavljena prilikom uploada
3. Kliknite na "Download"
4. Datoteka će biti preuzeta na vaše računalo

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
5. **Ne uploadajte osjetljive podatke** bez dodatne enkripcije.

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