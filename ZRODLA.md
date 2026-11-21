# Autorstwo i źródła

## Wkład autorów

| Autor | Wykonane elementy | Lokalizacja w projekcie |
| --- | --- | --- |
| Marcin Kowalczyk (Pixel of Software) | wybór biblioteki, założenia, przegląd i akceptacja kodu, publikacja | całość |
| Asystent AI Claude (Anthropic) | wrapper, adapter C, przykład, czytnik RSS/Atom, testy, dane testowe, skrypty budowania, dokumentacja | `app/`, `adapter/`, `przyklady/`, `tests/`, `dane/`, `build.py`, `run.py`, `README.md` |

## Wykorzystane materiały

| Materiał | Autor i źródło | Wersja lub data | Licencja | Sposób wykorzystania |
| --- | --- | --- | --- | --- |
| libxml2 | Daniel Veillard i współtwórcy, projekt GNOME, https://gitlab.gnome.org/GNOME/libxml2 | 2.9.13 (odniesienie z karty: 2.9.14) | MIT (https://github.com/GNOME/libxml2/blob/v2.9.14/Copyright) | biblioteka łączona dynamicznie, nie jest dołączona; deklaracje funkcji i opcje parsera według nagłówków `parser.h`, `xpath.h`, `xmlerror.h`, `tree.h` |
| XPath 1.0 | W3C Recommendation | 1999 | dokument W3C | semantyka wyników (string(), number(), boolean() zbioru węzłów) |
| RSS 2.0, Atom (RFC 4287), SVG | specyfikacje formatów | - | - | struktura przykładowych plików w `dane/` |
| `build.py`, `run.py`, `LICENSE` | Fundacja Duckling, szablon projektu z materiałów na start DuckQuest | 2026 | MIT (plik `LICENSE`) | skrypty rozbudowane o kompilację adaptera C, plik odpowiedzi linkera, cel `przyklad` i kopiowanie `dane/`; licencja z dopisanym autorem |
| Duckling (kompilator i biblioteka standardowa) | ducktype-org/duckling | 0.3-alpha, commit 83882805a | licencja Ducklinga | zależność budowania |

Pliki w `dane/` przygotowano dla tego projektu (fikcyjne kanały, katalog i rysunek). Plik `dane/rysunek.svg` zawiera dodatkowo blok metadanych pochodzenia (C2PA, element `<metadata>`), który środowisko pracy asystenta AI dołącza do tworzonych plików graficznych; nie wpływa on na testy (zapytania dotyczą elementów `rect`).

## Narzędzia AI

Kod wrappera i adaptera C, przykładu, czytnika i testów, dane testowe, zmiany skryptów budowania oraz dokumentację przygotowano z pomocą asystenta AI Claude (Anthropic). Autor ustalił zakres i wybór biblioteki, przejrzał wyniki, sprawdził działanie (budowa, 38 testów, przykład, czytnik, `leaks`) i odpowiada za oddaną wersję.

## Licencja własnego projektu

MIT, treść w pliku `LICENSE` (szablon Fundacji Duckling z dopisaną linią `Copyright (c) 2026 Pixel of Software (Marcin Kowalczyk)`). Licencja libxml2 dotyczy samej biblioteki, instalowanej osobno.
