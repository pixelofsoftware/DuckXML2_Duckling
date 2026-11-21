# Scenariusze sprawdzenia

Próby z 2026-11-21 na macOS 27.2 (Apple Silicon), `duckc 0.3-alpha (83882805a 2026-11-20)`, libxml2 2.9.13 (systemowa), Apple clang, wariant natywny, po `python3 build.py --target all --output build`.

| Scenariusz | Dane lub czynności | Oczekiwany wynik | Komenda lub procedura | Otrzymany wynik |
| --- | --- | --- | --- | --- |
| Parsowanie i element główny | `dane/katalog.xml`, tekst w przykładzie | `katalog`, `zamowienie`, puste URI przestrzeni | testy, przykład | zgodny - OK |
| Niepoprawny XML | `<a><b></a>`; `dane/uszkodzony.xml`; pusty; `<a>`; bajt 0xFF | kod 76 w wierszu 1; kod 76 w wierszu 5 (`title line 4 and channel`); kod 4; błąd; kod 9 `Input is not proper UTF-8` | testy, aplikacja | zgodny; aplikacja: kod 4 - OK |
| XPath: liczba i tekst | `count(//ksiazka)`, `sum(//cena)`, `string(//ksiazka[3]/tytul)`, `string(/katalog/@miasto)`, CDATA | 3; 89.5; `Quo vadis & inne`; `Kraków`; `Wydanie z <przypisami> i mapą` | testy | zgodny - OK |
| XPath: węzły | `//ksiazka[@dostepna='tak']/tytul`, `//ksiazka/@id` | 2 węzły ze ścieżkami `/katalog/ksiazka[1]/tytul`, `[3]` i wierszami 5, 15; 3 atrybuty | testy, aplikacja | zgodny - OK |
| Pusty wynik | `//nie_ma_takiego`; `//ksiazka[cena > 100]` | 0 węzłów, tekst pusty, NaN; aplikacja: kod 1 | testy, aplikacja | zgodny - OK |
| Błędne XPath | `//ksiazka[`, `nieznana(1)`, `//x:ksiazka`, puste | `ZLE_WYRAZENIE`: kod 1207 `Invalid expression` z pozycją; `Unregistered function`; `Undefined namespace prefix` | testy, aplikacja (`^` pod pozycją, kod 2) | zgodny - OK |
| Przestrzenie nazw | Atom (domyślna przestrzeń), SVG, RSS z `dc:` | `//entry` = 0, po rejestracji `//a:entry` = 2; 3 prostokąty, suma szerokości 97; 2 autorów `dc:creator` | testy, aplikacja | zgodny - OK |
| XXE | `dane/xxe.xml` z `<!ENTITY sekret SYSTEM "file:///etc/passwd">` | `ZABRONIONY`, plik nie jest czytany | testy, przykład, aplikacja | zgodny; 0 prób ładowania - OK |
| Bomba encji | `dane/bomba_encji.xml` (10^9 „lol”) | odrzucona bez rozwijania | testy | `NIEPOPRAWNY_XML: Detected an entity reference loop` - OK |
| Zewnętrzne DTD | `dane/zewnetrzne_dtd.xml` z `SYSTEM "http://..."` | dokument działa, bez pobierania | testy | zgodny - OK |
| Kopie i czas życia | wynik po `zwolnij`; `xpath` po zwolnieniu; podwójne `zwolnij`; dokument z błędem | kopie ważne; `ZAMKNIETY`; `false` | testy, przykład | zgodny - OK |
| Zwalnianie pamięci | testy (w tym 1000 cykli) pod `leaks --atExit` | 0 wycieków | `cd build && leaks --atExit -- ./tests-native/package_llvm.exe` | `0 leaks for 0 total leaked bytes` - OK |
| Kontrola ujemna | kopia bez `xmlFree` w kopiowaniu tekstów | `leaks` wykrywa wycieki | jak wyżej, na zmienionej kopii | `3039 leaks for 678368 total leaked bytes` - sprawdzenie działa |
| Praktyczne zastosowanie | czytnik na `dane/kanal_rss.xml` i `dane/kanal_atom.xml` | 3 wpisy RSS z datami i autorami (trzeci bez autora), 2 wpisy Atom | `printf 'dane/kanal_rss.xml\n\n' \| python3 run.py --build build --workdir .` | zgodny, kod 0 - OK |
| Testy | 38 sprawdzeń | `Bledy: 0`, kod 0 | `python3 run.py --build build --target tests` | `Bledy: 0` - OK |
| Odtworzenie w nowym katalogu | świeży klon repozytorium | budowa (z adapterem), przykład, czytnik i testy zgodne z README | `git clone`, komendy z README | macOS: OK; Linux x86_64 (Ubuntu 24.04, libxml2 2.9.14): nie sprawdzono |
