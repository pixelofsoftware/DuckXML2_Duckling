/*
 * Adapter C dla wrappera libxml2 w Ducklingu (moduł app/xml.dk).
 *
 * Potrzebny, bo:
 *  - xmlFree jest w libxml2 zmienną ze wskaźnikiem do funkcji, a nie funkcją;
 *  - pola struktur (xmlNode, xmlXPathObject, xmlError, xmlDtd) zależą od nagłówka,
 *    więc czytamy je tutaj, kompilując z nagłówkiem zainstalowanej biblioteki;
 *  - ustawienia bezpieczeństwa (odmowa ładowania zasobów zewnętrznych) i wyciszenie
 *    wypisywania błędów na stderr wymagają funkcji zwrotnych w C.
 * Diagnostyka jest od razu kopiowana do bufora wywołującego (opis), więc nie zależy
 * od kolejnych wywołań biblioteki.
 */
#include <string.h>
#include <libxml/parser.h>
#include <libxml/xmlmemory.h>
#include <libxml/xmlerror.h>
#include <libxml/xpath.h>
#include <libxml/xpathInternals.h>
#include <libxml/tree.h>
#include <libxml/hash.h>

static int odrzucone_ladowania = 0;

/* Każda próba załadowania zasobu zewnętrznego (DTD, encja, plik, URL) jest odrzucana. */
static xmlParserInputPtr odmow_ladowania(const char *url, const char *id, xmlParserCtxtPtr ctxt) {
    (void)url;
    (void)id;
    (void)ctxt;
    odrzucone_ladowania++;
    return NULL;
}

#if LIBXML_VERSION >= 21200
static void cichy_blad(void *dane, const xmlError *blad) { (void)dane; (void)blad; }
#else
static void cichy_blad(void *dane, xmlErrorPtr blad) { (void)dane; (void)blad; }
#endif

static void cichy_ogolny(void *ctx, const char *msg, ...) { (void)ctx; (void)msg; }

/* Pierwszy błąd parsowania (libxml2 zapamiętuje w kontekście tylko ostatni, a pierwszy
 * zwykle lepiej wskazuje przyczynę, np. niezgodny znacznik zamykający). */
typedef struct {
    int kod;
    int wiersz;
    int kolumna;
    char opis[512];
} pierwszy_blad_t;

static void kopiuj_opis(const char *zrodlo, char *opis, int rozmiar);

static void zapamietaj(pierwszy_blad_t *p, const xmlError *b) {
    if (p == NULL || b == NULL || p->kod != 0 || b->level < XML_ERR_ERROR) return;
    p->kod = b->code;
    p->wiersz = b->line;
    p->kolumna = b->int2;
    kopiuj_opis(b->message, p->opis, (int)sizeof(p->opis));
}

#if LIBXML_VERSION >= 21200
static void zapisz_pierwszy(void *dane, const xmlError *blad) { zapamietaj((pierwszy_blad_t *)dane, blad); }
#else
static void zapisz_pierwszy(void *dane, xmlErrorPtr blad) { zapamietaj((pierwszy_blad_t *)dane, blad); }
#endif

void dkxml_init(void) {
    xmlInitParser();
    xmlSetExternalEntityLoader(odmow_ladowania);
    xmlSetStructuredErrorFunc(NULL, cichy_blad);
    xmlSetGenericErrorFunc(NULL, cichy_ogolny);
}

int dkxml_refused_loads(void) { return odrzucone_ladowania; }

const char *dkxml_version(void) { return xmlParserVersion; }

void dkxml_free(void *p) {
    if (p != NULL) xmlFree(p);
}

static void kopiuj_opis(const char *zrodlo, char *opis, int rozmiar) {
    size_t n;
    if (rozmiar <= 0) return;
    opis[0] = '\0';
    if (zrodlo == NULL) return;
    strncpy(opis, zrodlo, (size_t)rozmiar - 1);
    opis[rozmiar - 1] = '\0';
    n = strlen(opis);
    while (n > 0 && (opis[n - 1] == '\n' || opis[n - 1] == ' ')) opis[--n] = '\0';
}

/* Parsowanie z pamięci; przy błędzie kopiuje kod, wiersz, kolumnę i komunikat. */
xmlDocPtr dkxml_parse(const char *bufor, int dlugosc, int opcje, int *kod, int *wiersz,
                      int *kolumna, char *opis, int rozmiar) {
    xmlParserCtxtPtr ctxt;
    xmlDocPtr doc;
    *kod = 0;
    *wiersz = 0;
    *kolumna = 0;
    kopiuj_opis(NULL, opis, rozmiar);
    ctxt = xmlNewParserCtxt();
    if (ctxt == NULL) {
        *kod = -2;
        kopiuj_opis("brak pamieci na kontekst parsera", opis, rozmiar);
        return NULL;
    }
    pierwszy_blad_t pierwszy;
    memset(&pierwszy, 0, sizeof(pierwszy));
    xmlSetStructuredErrorFunc(&pierwszy, zapisz_pierwszy);
    doc = xmlCtxtReadMemory(ctxt, bufor, dlugosc, "dokument.xml", "UTF-8", opcje);
    xmlSetStructuredErrorFunc(NULL, cichy_blad);
    if (doc == NULL && pierwszy.kod != 0) {
        *kod = pierwszy.kod;
        *wiersz = pierwszy.wiersz;
        *kolumna = pierwszy.kolumna;
        kopiuj_opis(pierwszy.opis, opis, rozmiar);
    } else if (doc == NULL) {
        const xmlError *b = (const xmlError *)xmlCtxtGetLastError(ctxt);
        if (b != NULL) {
            *kod = b->code;
            *wiersz = b->line;
            *kolumna = b->int2;
            kopiuj_opis(b->message, opis, rozmiar);
        }
        if (*kod == 0) *kod = -1;
    }
    xmlFreeParserCtxt(ctxt);
    return doc;
}

/* Liczba encji zadeklarowanych w wewnętrznym DTD (ogólnych i parametrycznych). */
int dkxml_entity_count(xmlDocPtr doc) {
    int n = 0;
    if (doc == NULL || doc->intSubset == NULL) return 0;
    if (doc->intSubset->entities != NULL) n += xmlHashSize((xmlHashTablePtr)doc->intSubset->entities);
    if (doc->intSubset->pentities != NULL) n += xmlHashSize((xmlHashTablePtr)doc->intSubset->pentities);
    return n;
}

const char *dkxml_node_name(xmlNodePtr n) {
    return (n != NULL && n->name != NULL) ? (const char *)n->name : "";
}

const char *dkxml_node_ns(xmlNodePtr n) {
    return (n != NULL && n->ns != NULL && n->ns->href != NULL) ? (const char *)n->ns->href : "";
}

int dkxml_node_type(xmlNodePtr n) { return n != NULL ? (int)n->type : 0; }

/* Obliczenie wyrażenia XPath; przy błędzie kopiuje kod, pozycję w wyrażeniu i komunikat. */
xmlXPathObjectPtr dkxml_xpath(xmlXPathContextPtr ctx, const char *wyrazenie, int *kod,
                              int *pozycja, char *opis, int rozmiar) {
    xmlXPathObjectPtr wynik;
    *kod = 0;
    *pozycja = -1;
    kopiuj_opis(NULL, opis, rozmiar);
    xmlResetLastError();
    wynik = xmlXPathEvalExpression((const xmlChar *)wyrazenie, ctx);
    if (wynik == NULL) {
        const xmlError *b = (const xmlError *)xmlGetLastError();
        if (b != NULL) {
            *kod = b->code;
            *pozycja = b->int1;
            kopiuj_opis(b->message, opis, rozmiar);
        }
        if (*kod == 0) *kod = -1;
    }
    return wynik;
}

int dkxml_obj_type(xmlXPathObjectPtr o) { return o != NULL ? (int)o->type : 0; }

int dkxml_nodeset_count(xmlXPathObjectPtr o) {
    if (o == NULL || o->type != XPATH_NODESET || o->nodesetval == NULL) return 0;
    return o->nodesetval->nodeNr;
}

xmlNodePtr dkxml_nodeset_item(xmlXPathObjectPtr o, int i) {
    if (i < 0 || i >= dkxml_nodeset_count(o)) return NULL;
    return o->nodesetval->nodeTab[i];
}
