# DuckXML2: wrapper libxml2 dla Ducklinga

![Napisane w Duckling](https://img.shields.io/badge/napisane%20w-Duckling-f2c94c)

Zespół: Pixel of Software (Marcin Kowalczyk). Temat: P02 DuckBridge, biblioteka libxml2 (poziom 3). Skład: 1 osoba.

Moduł `xml` (`app/xml.dk`) parsuje dokumenty XML z tekstu lub bajtów UTF-8 i wykonuje na nich zapytania XPath przez libxml2. Wyniki zapytań są własnymi kopiami danych: liczby, teksty, wartości logiczne oraz węzły z nazwą, tekstem, ścieżką i numerem wiersza. Użytkownik nie dostaje żadnego wskaźnika do drzewa dokumentu. Parser jest domyślnie zamknięty: nie łączy się z siecią, nie ładuje zewnętrznych DTD i nie rozwija encji. Dokumenty z deklaracjami encji odrzuca jako niebezpieczne (XXE, „bomba encji”).

Całe minimum karty libxml2 działa i jest sprawdzone testami. Do tego są dwa przykłady: podstawowy i czytnik kanałów RSS/Atom z narzędziem do zapytań XPath jako praktyczne zastosowanie. Rozszerzenia:
* przestrzenie nazw w XPath (Atom, SVG, Dublin Core);
* węzły-atrybuty;
* ścieżki i numery wierszy węzłów;
* odczyt pliku wyłącznie przez wrapper;
* licznik odrzuconych prób ładowania zasobów.

## Uruchomienie

Wymagane są:
* Python 3;
* Duckling (`duckc` w `PATH`, instalacja według tutoriala);
* kompilator C (`cc`);
* libxml2 2.9 lub nowsza **z nagłówkami**, bo adapter C jest kompilowany podczas budowania.

| System | Instalacja |
| --- | --- |
| Ubuntu | `sudo apt install build-essential libxml2-dev` |
| macOS | Xcode Command Line Tools (`xcode-select --install`); libxml2 jest częścią systemu |

Z katalogu projektu:

```bash
python3 build.py --target all --output build      # adapter C, aplikacja, przykład i testy; kopiuje dane/ do build/
python3 run.py --build build --target tests       # testy: PASS/FAIL, kod = liczba błędów
python3 run.py --build build --target przyklad    # przykład podstawowy
printf 'dane/kanal_rss.xml\n\n' | python3 run.py --build build --workdir .                       # czytnik kanału
printf "dane/katalog.xml\n//ksiazka[@dostepna='tak']/tytul\n" | python3 run.py --build build --workdir .   # zapytanie XPath
```

Aplikacja czyta dwa wiersze ze standardowego wejścia:
1. plik XML;
2. wyrażenie XPath albo pusty wiersz.

Przy pustym wierszu rozpoznaje kanał RSS 2.0 (`<rss>`) albo Atom (`<feed>` w przestrzeni Atom) i wypisuje tytuł kanału oraz wpisy: tytuł, odnośnik, datę i autora. Z wyrażeniem wypisuje typ wyniku, wartość i węzły z numerami wierszy. W zapytaniach działają prefiksy:

| Prefiks | Przestrzeń nazw |
| --- | --- |
| `a` | Atom |
| `dc` | Dublin Core |
| `svg` | SVG |

Kody zakończenia:

| Kod | Znaczenie |
| --- | --- |
| 0 | jest wynik |
| 1 | pusty wynik |
| 2 | złe wyrażenie |
| 3 | błąd pliku |
| 4 | niepoprawny albo odrzucony dokument |

`build.py` kompiluje `adapter/xml_adapter.c`. Ścieżkę do nagłówków próbuje wziąć z `xml2-config` i `pkg-config`, a potem z typowych katalogów i SDK macOS. Adapter i bibliotekę (`-lxml2` albo plik podany przez `--xml2`) przekazuje do `duckc` przez plik odpowiedzi linkera (`--additional-link-options @build/adapter/linker.rsp`), bo `duckc` przyjmuje tylko jedną opcję linkera. `build.py` i `run.py` powstały z szablonu konkursu: doszły kompilacja adaptera, cel `przyklad` i kopiowanie `dane/` do katalogu budowy.

## Funkcje i demonstracja

| Funkcja z minimum karty | Sposób uruchomienia | Oczekiwany rezultat |
| --- | --- | --- |
| Parsowanie z bajtów/tekstu UTF-8, element główny, czytelny błąd | przykład; aplikacja na `dane/uszkodzony.xml` | `Element glowny: zamowienie`; `NIEPOPRAWNY_XML, kod 76, wiersz 2: Opening and ending tag mismatch: b line 2 and c`; aplikacja: `w wierszu 5, kolumnie 13`, kod 4 |
| Dokument i kontekst XPath, wynik tekstowy i liczbowy | przykład | `Liczba sztuk: 3; numer zamowienia: 2026/11/07`; `//pozycja: 2 wezly` ze ścieżkami |
| Wyniki jako kopie, czas życia, brak wskaźników do zwolnionego drzewa | przykład, testy | `Po zwolnieniu dokumentu wyniki nadal sa kopiami: 'Staw dmuchany'`; zapytanie do zwolnionego dokumentu: `ZAMKNIETY` |
| Bez sieci, bez zewnętrznego DTD i bez rozwijania encji zewnętrznych | przykład, testy, aplikacja na `dane/xxe.xml` | `Dokument z encja zewnetrzna (XXE): ZABRONIONY`; DTD z `http://...` nie jest pobierane |
| Zwalnianie przez funkcje biblioteki (`xmlFree`, `xmlXPathFreeObject`, `xmlXPathFreeContext`, `xmlFreeDoc`), kopiowanie diagnostyki | testy, `leaks` (macOS) | 0 wycieków; kontrola ujemna bez `xmlFree` daje 3039 wycieków |
| Praktyczne zastosowanie | aplikacja na `dane/kanal_rss.xml` i `dane/kanal_atom.xml` | 3 wpisy RSS (z autorem `dc:creator`), 2 wpisy Atom |

**Demonstracja:**
1. Uruchom przykład.
2. Uruchom czytnik na `dane/kanal_rss.xml`: polskie tytuły, daty i autorzy z przestrzeni nazw Dublin Core.
3. Uruchom czytnik na `dane/kanal_atom.xml`, czyli kanale z domyślną przestrzenią nazw.
4. Zapytaj `dane/rysunek.svg` wyrażeniem `sum(//svg:rect/@width)`. Wynik to `97`.
5. Podaj błędne wyrażenie, np. `//ksiazka[@id=`. Dostaniesz kod 1207 i znacznik `^` pod pozycją błędu.
6. Uruchom czytnik na `dane/xxe.xml`. Dokument zostanie odrzucony jako `ZABRONIONY`.

## API modułu `xml`

| Funkcja | Zwraca | Błąd (`rodzaj`) |
| --- | --- | --- |
| `parsuj(tekst: str) -> Dokument` | dokument z `korzen` i `przestrzenKorzenia` (kopie) | `NIEPOPRAWNY_XML` (`blad.kod`, `blad.wiersz`, `blad.kolumna`, `blad.opis` z libxml2), `ZABRONIONY`, `ZA_DUZY`, `BRAK_PAMIECI` |
| `parsujBajty(dane: ref List[u8]) -> Dokument` | jak wyżej, z bajtów | jak wyżej |
| `parsujPlik(sciezka) -> Dokument` | wrapper czyta plik do pamięci (najwyżej 64 MiB) i go parsuje | dodatkowo `BLAD_PLIKU` |
| `xpath(d: ref Dokument, wyrazenie) -> Wynik` | `typ` (`WEZLY`, `LOGICZNY`, `LICZBA`, `TEKST`), `tekst`, `liczba`, `logiczny`, `wezly: List[Wezel]` | `ZLE_WYRAZENIE` (`blad.kod`, `blad.kolumna` = pozycja w wyrażeniu, `blad.opis`), `ZAMKNIETY`, `ZA_DUZY` |
| `tekstXPath(d, w) -> String`, `liczbaXPath(d, w) -> f64` | skróty: `string()` i `number()` wyniku | pusty tekst / NaN |
| `zarejestrujPrzestrzen(d, prefiks, uri) -> bool` | prefiks do użycia w XPath | `false` dla zwolnionego dokumentu |
| `zwolnij(d: ref Dokument) -> bool` | zwalnia kontekst i drzewo | `false`, gdy nie było czego zwalniać |
| `aktywny`, `nazwaRodzaju`, `nazwaTypu`, `jestNaN`, `wersjaBiblioteki`, `odrzuconeLadowania` | pomocnicze | - |

`Wezel` zawiera:
* `typ` (`ELEMENT`, `ATRYBUT`, `WEZEL_TEKSTOWY`, …);
* `nazwa`, `przestrzen` (URI);
* `tekst` - dla elementu cały tekst potomków razem z CDATA, dla atrybutu jego wartość;
* `sciezka`, np. `/katalog/ksiazka[3]/tytul`;
* `wiersz`.

Wynik typu `WEZLY` jako `tekst` daje tekst pierwszego węzła, a jako `logiczny` - informację, czy zbiór jest niepusty, zgodnie z regułami XPath 1.0.

## Pamięć i czas życia

| Obiekt | Kto tworzy | Kto zwalnia |
| --- | --- | --- |
| drzewo dokumentu (`xmlDoc`) | `parsuj*` | `zwolnij`, przez `xmlFreeDoc` |
| kontekst XPath (`xmlXPathContext`) | `parsuj*`, jeden na dokument | `zwolnij`, przez `xmlXPathFreeContext`, **przed** drzewem |
| wynik XPath (`xmlXPathObject`) | `xpath` | `xpath`, przez `xmlXPathFreeObject`, zanim zwróci kopie |
| teksty z `xmlNodeGetContent`, `xmlGetNodePath`, `xmlXPathCastToString` | libxml2 | wrapper, przez `xmlFree` w adapterze (nie zwykłym `free`) |
| diagnostyka (`xmlError`) | libxml2 | adapter od razu kopiuje kod, wiersz, kolumnę i komunikat do bufora wywołującego |

Moduł **nie udostępnia widoków**: każdy `Wynik` i `Wezel` to zwykłe wartości Ducklinga, ważne bez ograniczeń, także po `zwolnij`. Po zwolnieniu `xpath` zwraca `ZAMKNIETY`, a ponowne `zwolnij` zwraca `false`. Dokumentu nie należy kopiować przez `copy`, bo kopia wskazywałaby to samo drzewo. Parser zapamiętuje pierwszy błąd w dokumencie, a nie ostatni: przy `<a><b></a>` dostajesz niezgodny znacznik zamykający (kod 76), a nie dalszy błąd „Premature end of data”. Program testów pod `leaks --atExit` na macOS zgłasza 0 wycieków.

## Bezpieczeństwo i obsługiwany zakres

Dokument jest parsowany z pamięci z opcjami `XML_PARSE_NONET | XML_PARSE_NOERROR | XML_PARSE_NOWARNING`. Celowo **bez** tych opcji:
* `XML_PARSE_NOENT` - podstawianie encji;
* `XML_PARSE_DTDLOAD` - ładowanie zewnętrznego DTD;
* `XML_PARSE_DTDATTR`;
* `XML_PARSE_XINCLUDE`;
* `XML_PARSE_HUGE`.

Dodatkowo adapter ustawia `xmlSetExternalEntityLoader` na funkcję, która odrzuca **każdą** próbę załadowania pliku lub adresu i liczy takie próby (`odrzuconeLadowania`).

| Dokument | Zachowanie |
| --- | --- |
| zwykły XML, CDATA, komentarze, przestrzenie nazw | obsługiwany |
| encje wbudowane (`&amp;`, `&lt;`, …) i odwołania znakowe (`&#261;`) | obsługiwane |
| `<!DOCTYPE x SYSTEM "http://...">` (zewnętrzne DTD) | dokument działa, DTD nie jest pobierane ani sprawdzane |
| `<!ENTITY ...>` w wewnętrznym DTD, także `SYSTEM "file:///etc/passwd"` (XXE) | odrzucony: `ZABRONIONY` |
| „bomba encji” (10⁹ powtórzeń) | odrzucona przez libxml2 (`Detected an entity reference loop`) albo przez wrapper |
| inne kodowanie niż UTF-8 | dane są czytane jako UTF-8, a deklaracja kodowania jest ignorowana; niepoprawny UTF-8 to błąd z opisem |
| walidacja DTD/XML Schema, XInclude, XSLT, modyfikacja drzewa | poza zakresem |

Pojedynczy dokument ma limit 64 MiB, a wynik może mieć najwyżej 1 000 000 węzłów. Ustawienia błędów w libxml2 są globalne, więc modułu nie należy używać równolegle z wielu wątków.

## Środowisko i zależności

| Element | Wartość |
| --- | --- |
| Kompilator | `duckc 0.3-alpha (83882805a 2026-11-20)`, `commit-hash: 83882805a` |
| Uruchomienie | natywnie |
| System operacyjny | macOS 27.2, Apple Silicon (arm64), Apple clang |
| Zależności | libxml2 2.9.13 (systemowa, `/usr/lib/libxml2.2.dylib`, nagłówki z SDK macOS), Python 3 |

Wersja odniesienia z karty to libxml2 2.9.14. API i pola struktur użyte w adapterze są w 2.9.13 i 2.9.14 takie same. Adapter ma też warianty sygnatur funkcji zwrotnych dla libxml2 2.12 i nowszych (`const xmlError *`), ale tych wersji nie sprawdzałem. Na Linuksie x86_64 (Ubuntu 24.04, libxml2 2.9.14) projektu nie sprawdzałem.

## Struktura i działanie

| Plik | Odpowiedzialność |
| --- | --- |
| `app/xml.dk` | wrapper: deklaracje C, typy `Dokument`, `Wynik`, `Wezel`, `BladXml`, parsowanie, XPath, kopiowanie, zwalnianie |
| `adapter/xml_adapter.c` | adapter C (ok. 180 wierszy): `xmlFree`, odczyt pól struktur, pierwszy błąd parsowania, błędy XPath, odmowa ładowania zasobów, wyciszenie stderr |
| `app/app.dk` | praktyczne zastosowanie: czytnik RSS/Atom i narzędzie do zapytań XPath |
| `przyklady/podstawowy.dk` | przykład podstawowy |
| `tests/testy.dk` | testy parsowania, XPath, przestrzeni nazw, bezpieczeństwa i pamięci |
| `dane/` | katalog, kanały RSS i Atom, rysunek SVG, uszkodzony XML, XXE, bomba encji, zewnętrzne DTD |

**Adapter C** jest potrzebny, bo:
* `xmlFree` jest w libxml2 zmienną ze wskaźnikiem do funkcji;
* pola `xmlNode`, `xmlXPathObject`, `xmlError` i `xmlDtd` zależą od nagłówka;
* odmowa ładowania i przechwytywanie błędów wymagają funkcji zwrotnych.

Pozostałe funkcje wrapper wywołuje bezpośrednio: `xmlDocGetRootElement`, `xmlXPathNewContext`, `xmlXPathRegisterNs`, `xmlXPathCastTo*`, `xmlNodeGetContent`, `xmlGetNodePath`, `xmlGetLineNo` i funkcje zwalniające. Wskaźniki są przechowywane jako `u64`, czego dotyczy ABI LP64. Wariant DVM nie jest obsługiwany.

## Sprawdzenie projektu

```bash
python3 run.py --build build --target tests      # 38 sprawdzeń
python3 run.py --build build --target przyklad   # kod 0 = wszystkie oczekiwania przykładu spełnione
```

Testy sprawdzają:
* element główny, encje wbudowane i odwołania znakowe;
* błędy z kodem, wierszem i opisem: złe zagnieżdżenie, niedomknięty plik, pusty dokument, niepoprawny UTF-8, brak pliku;
* XPath: `count`, `sum`, `string`, atrybuty z polskimi literami, CDATA, zbiory węzłów ze ścieżkami i wierszami, atrybuty jako węzły, wyniki logiczne i tekstowe, pusty zbiór (NaN);
* błędne wyrażenia: składnia, nieznana funkcja, nieznany prefiks, puste;
* przestrzenie nazw Atom, SVG i Dublin Core;
* XXE, bombę encji i zewnętrzne DTD;
* kopie po zwolnieniu, `ZAMKNIETY` i podwójne zwolnienie;
* 1000 cykli parsowania, zapytania i błędów.

Scenariusze są w [tests/scenariusze.md](tests/scenariusze.md).

## Autorstwo i materiały

Kod i dokumentacja: Pixel of Software (Marcin Kowalczyk), z pomocą asystenta AI. Szczegóły są w [ZRODLA.md](ZRODLA.md).

Licencja własnego kodu: MIT (plik `LICENSE`). Biblioteka libxml2 ma licencję MIT i nie jest dołączona do repozytorium; wrapper i adapter łączą się z nią dynamicznie.
