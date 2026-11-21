#!/usr/bin/env python3
"""Zbuduj aplikację, przykład i testy wrappera libxml2; komendy uruchomienia zapisz w budowa.json.

Skrypt na bazie build.py z szablonu konkursu DuckQuest (Fundacja Duckling, MIT). Zmiany:
kompilacja adaptera C (adapter/xml_adapter.c) z nagłówkami libxml2, dołączanie adaptera
i biblioteki libxml2 przez plik odpowiedzi linkera (@plik), cel "przyklad"
(przyklady/podstawowy.dk), kopia katalogu dane/ do katalogu budowy i wyłącznie wariant natywny.
Nie pobiera i nie instaluje paczek.
"""

import argparse
import json
from pathlib import Path
import shlex
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent
ENTRIES = {"app": None, "tests": ROOT / "tests/testy.dk", "przyklad": ROOT / "przyklady/podstawowy.dk"}
REPORT = "budowa.json"
ADAPTER = ROOT / "adapter/xml_adapter.c"
INSTALL_HINT = ("zainstaluj libxml2 z nagłówkami (Ubuntu: sudo apt install libxml2-dev; "
                "macOS: Xcode Command Line Tools) oraz kompilator C (cc)")


def execute(command, cwd):
    command = [str(part) for part in command]
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=180)


def find_tool(path, name, option):
    """Zwróć ścieżkę podaną wprost albo narzędzie z PATH (instalacja według tutoriala)."""
    if path is None:
        found = shutil.which(name)
        if found is None:
            raise ValueError(f"Nie znaleziono {name} w PATH. Zainstaluj Ducklinga według "
                             f"tutoriala albo wskaż narzędzie przez {option}.")
        path = Path(found)
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"Nie znaleziono {name}: {path}")
    return path


def output_of(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def compile_flags():
    """Kandydaci na flagi kompilatora z nagłówkami libxml2 (sprawdzani kompilacją adaptera)."""
    candidates = []
    for command in (["xml2-config", "--cflags"], ["pkg-config", "--cflags", "libxml-2.0"]):
        flags = output_of(command)
        if flags is not None:
            candidates.append(shlex.split(flags))
            for flag in shlex.split(flags):
                if flag.startswith("-I") and not flag.rstrip("/").endswith("libxml2"):
                    candidates.append([flag + "/libxml2"])
    for path in ("/usr/include/libxml2", "/usr/local/include/libxml2", "/opt/homebrew/opt/libxml2/include/libxml2"):
        candidates.append(["-I" + path])
    sdk = output_of(["xcrun", "--show-sdk-path"])
    if sdk:
        candidates.append(["-I" + sdk + "/usr/include/libxml2"])
    return candidates


def link_flags(explicit):
    """Opcje linkera dla libxml2: plik podany wprost albo -L/-l z pkg-config/xml2-config."""
    if explicit:
        if not explicit.is_file():
            raise ValueError(f"Nie znaleziono biblioteki {explicit}")
        return [str(explicit.resolve())]
    for command in (["pkg-config", "--libs", "libxml-2.0"], ["xml2-config", "--libs"]):
        flags = output_of(command)
        if flags:
            return [f for f in shlex.split(flags) if f.startswith("-L") or f == "-lxml2"] or ["-lxml2"]
    return ["-lxml2"]


def build_adapter(cc, output):
    """Skompiluj adapter C; zwróć plik .o i użyte flagi."""
    target = output / "adapter" / "xml_adapter.o"
    target.parent.mkdir(parents=True)
    errors = []
    for flags in compile_flags():
        result = execute([cc, "-O2", "-fPIC", "-Wall", "-c", ADAPTER, "-o", target] + flags, output)
        if result.returncode == 0 and target.is_file():
            return target, flags
        errors.append(" ".join(flags) + ": " + result.stderr.strip().splitlines()[0] if result.stderr.strip() else " ".join(flags))
    raise ValueError("nie udało się skompilować adaptera C - " + INSTALL_HINT + "\n" + "\n".join(errors[:4]))


def version(tool, option):
    result = execute([tool, option], ROOT)
    if result.returncode != 0:
        raise ValueError(f"{tool} {option} zwrócił kod {result.returncode}:\n{result.stderr}")
    return result.stdout


def prepare_output(output):
    """Usuń poprzednią budowę albo pusty katalog; katalogu z innymi plikami nie ruszaj."""
    if output.is_dir() and ((output / REPORT).is_file() or not any(output.iterdir())):
        shutil.rmtree(output)
    elif output.exists():
        raise ValueError(f"{output} nie jest katalogiem budowy; wybierz inny --output.")
    output.mkdir(parents=True)


def package(output, target):
    """Zwróć katalog pakietu: źródła aplikacji albo ich kopię z innym punktem wejścia."""
    if ENTRIES[target] is None:
        return ROOT / "app"
    path = output / f"pakiet-{target}" / "app"
    shutil.copytree(ROOT / "app", path)
    shutil.copy2(ENTRIES[target], path / "app.dk")
    return path


def build(args):
    targets = ("app", "przyklad", "tests") if args.target == "all" else (args.target,)
    duckc = find_tool(args.duckc, "duckc", "--duckc")
    cc = find_tool(args.cc, "cc", "--cc")
    report = {"ok": False, "tools": {}, "adapter": {}, "compilation": {}, "commands": {}}
    report["tools"]["duckc"] = version(duckc, "--version-verbose")

    output = args.output.resolve()
    prepare_output(output)
    shutil.copytree(ROOT / "dane", output / "dane")
    try:
        adapter, flags = build_adapter(cc, output)
        libs = link_flags(args.xml2)
        response = output / "adapter" / "linker.rsp"
        response.write_text("\n".join([str(adapter)] + libs) + "\n", encoding="utf-8")
        report["adapter"] = {"cc": str(cc), "cflags": flags, "link": libs}
        print(f"PASS adapter ({' '.join(flags)})", flush=True)
        for target in targets:
            source = package(output, target)
            name = f"{target}-native"
            artifacts = output / name
            command = [duckc, "compile_package", source, "-n", "app", "-a", artifacts,
                       "--custom-std-artifacts-path", output / "std",
                       "--additional-link-options", f"@{response}"]
            if args.std:
                command += ["--custom-std-path", args.std.resolve()]
            result = execute(command, output)
            report["compilation"][name] = result.stderr + result.stdout
            binary = artifacts / "package_llvm.exe"
            passed = result.returncode == 0 and binary.is_file()
            print(("PASS " if passed else "FAIL ") + name, flush=True)
            if not passed:
                raise ValueError(f"kompilacja {name} nie powiodła się.\n{result.stderr}{result.stdout}")
            report["commands"][name] = [str(binary)]
        report["ok"] = True
        print(f"biblioteka: {' '.join(libs)}", flush=True)
    finally:
        text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        (output / REPORT).write_text(text, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duckc", type=Path, help="Kompilator; domyślnie duckc z PATH.")
    parser.add_argument("--cc", type=Path, help="Kompilator C dla adaptera; domyślnie cc z PATH.")
    parser.add_argument("--xml2", type=Path, help="Plik biblioteki libxml2 (.so albo .dylib); domyślnie -lxml2.")
    parser.add_argument("--std", type=Path,
                        help="Źródła zgodnej biblioteki standardowej, jeśli nie są ustawione w duckc.")
    parser.add_argument("--target", choices=("app", "przyklad", "tests", "all"), default="app")
    parser.add_argument("--output", type=Path, default=ROOT / "build",
                        help="Katalog wyników; poprzednia budowa w nim zostanie zastąpiona.")
    args = parser.parse_args()
    try:
        build(args)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"Błąd budowania: {error}\n")


if __name__ == "__main__":
    main()
