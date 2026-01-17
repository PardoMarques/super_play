#!/usr/bin/env python3
"""CLI de automação com comando doctor."""

import argparse
import sys
from pathlib import Path

from project.core import get_config, create_run_dirs, generate_run_id, get_logger


def cmd_doctor(args):
    """
    Comando doctor - verifica setup e imprime configuração.
    
    Cria um diretório de teste para verificar se tudo funciona.
    """
    logger = get_logger("doctor")
    
    logger.info("Executando verificação doctor...")
    
    # Carrega configuração
    config = get_config()
    
    # Gera run ID e cria diretórios
    run_id = generate_run_id()
    dirs = create_run_dirs(config.artifacts_dir, run_id)
    
    # Imprime configuração
    print("\n" + "=" * 50)
    print("CONFIGURAÇÃO")
    print("=" * 50)
    print(f"  BASE_URL:      {config.base_url or '(not set)'}")
    print(f"  ARTIFACTS_DIR: {config.artifacts_dir.absolute()}")
    print()
    
    print("=" * 50)
    print("DIRETÓRIOS DE TESTE CRIADOS")
    print("=" * 50)
    for name, path in dirs.items():
        exists = "✓" if path.exists() else "✗"
        print(f"  [{exists}] {name}: {path.absolute()}")
    print()
    
    logger.info("Verificação doctor concluída!")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Super Play automation CLI"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")
    
    # Comando doctor
    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Verifica setup e imprime configuração"
    )
    doctor_parser.set_defaults(func=cmd_doctor)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
