def realizar_requisicao(
    payload: dict
) -> requests.Response:
    ultimo_erro: Exception | None = None

    for tentativa in range(
        1,
        TENTATIVAS_MAXIMAS + 1
    ):
        try:
            print(
                f">>> Tentativa {tentativa}/"
                f"{TENTATIVAS_MAXIMAS} de conexão com a Groq",
                flush=True
            )

            resposta = requests.post(
                URL_GROQ,
                headers={
                    "Authorization": (
                        f"Bearer {GROQ_API_KEY}"
                    ),
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=(
                    TIMEOUT_CONEXAO,
                    TIMEOUT_RESPOSTA,
                ),
            )

            print(
                f">>> Groq respondeu com HTTP "
                f"{resposta.status_code}",
                flush=True
            )

            return resposta

        except requests.RequestException as erro:
            ultimo_erro = erro

            print(
                "\n========== ERRO DE REDE ==========",
                flush=True
            )
            print(
                f"Tipo: {type(erro).__name__}",
                flush=True
            )
            print(
                f"Detalhes: {erro!r}",
                flush=True
            )
            print(
                "==================================\n",
                flush=True
            )

            if tentativa < TENTATIVAS_MAXIMAS:
                espera = 2 * tentativa

                print(
                    f">>> Nova tentativa em "
                    f"{espera} segundos...",
                    flush=True
                )

                time.sleep(espera)

        except Exception as erro:
            print(
                "\n========== ERRO INESPERADO ==========",
                flush=True
            )
            print(
                f"Tipo: {type(erro).__name__}",
                flush=True
            )
            print(
                f"Detalhes: {erro!r}",
                flush=True
            )
            print(
                "=====================================\n",
                flush=True
            )

            raise RuntimeError(
                "Erro inesperado ao preparar a conexão "
                f"com a Groq: {erro}"
            ) from erro

    raise RuntimeError(
        "Não foi possível conectar à Groq após "
        f"{TENTATIVAS_MAXIMAS} tentativas. "
        f"Último erro: {type(ultimo_erro).__name__}: "
        f"{ultimo_erro}"
    )