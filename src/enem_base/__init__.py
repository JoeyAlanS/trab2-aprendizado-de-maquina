"""Preparação de dados e contratos independentes da escolha do alvo."""

import os
from pathlib import Path

__version__ = "0.1.0"

# Em sandboxes Flatpak (ex.: terminal do VS Code Flatpak), o OpenSSL embutido no
# libarrow lê o openssl.cnf do runtime e carrega um engine pkcs11 incompatível,
# encerrando o processo com falha de segmentação ao importar pyarrow. Uma
# configuração vazia evita o engine sem afetar HTTPS nem os dados. Precisa ocorrer
# antes do primeiro import de pyarrow; uma escolha explícita do usuário é mantida.
if Path("/.flatpak-info").exists():
    os.environ.setdefault("OPENSSL_CONF", os.devnull)
