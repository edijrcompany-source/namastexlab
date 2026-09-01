"""Turn orchestrator — junta LLM + extração + price-guard + máquina de estados
+ ACL + catálogo (spec §1, §4, §6). O núcleo do Agente.

Executa um turno por chamada, de forma determinística entre injeções
(LLM/ACL/store trocáveis — FakeLLM + ACL mockada nos testes, offline).
"""

from __future__ import annotations

from app.conversation.models import Conversa, Mensagem
from app.conversation.state_machine import Efeito, Estado, Evento, criar_conversa, transitar
from app.domain.extraction import Campos
from app.domain.ids import ulid
from app.domain.ports import LLMPort
from app.events.store import InMemoryStore, Store
from app.formatting import format_brl
from app.i18n import carregar, t
from app.privacy.masking import mask_for_llm, mask_for_output


class TurnOrchestrator:
    def __init__(
        self,
        llm: LLMPort,
        acl: object | None = None,
        store: Store | None = None,
        catalogo: dict | None = None,
    ) -> None:
        self._llm = llm
        self._acl = acl
        self._store = store or InMemoryStore()
        self._cat = catalogo if catalogo is not None else carregar()
        self._planos: list[dict] | None = None

    @property
    def store(self) -> Store:
        return self._store

    # ── ciclo de vida ────────────────────────────────────────────────────
    def iniciar(self, correlation_id: str | None = None) -> Conversa:
        inicio = criar_conversa()
        conversa = Conversa(id=ulid(), estado=inicio.estado, correlation_id=correlation_id)
        conversa.registrar_evento("conversation_started")
        self._responder(conversa, inicio.efeitos)
        self._store.salvar(conversa)
        return conversa

    def processar(
        self,
        conversation_id: str,
        texto: str | None = None,
        midia: tuple[str, str] | None = None,
    ) -> Conversa:
        conversa = self._store.obter(conversation_id)
        if conversa is None:
            raise KeyError(conversation_id)

        if conversa.estado is Estado.HANDOFF:
            # absorvente (invariável I2): idempotente, sem LLM e sem transição
            conversa.historico.append(Mensagem("lead", "text", mask_for_output(texto or "")))
            self._responder_texto(conversa, t("agent.aguardando_humano_idempotente", self._cat))
            self._store.salvar(conversa)
            return conversa
        if conversa.estado.value.startswith("ENCERRADA"):
            conversa.historico.append(Mensagem("lead", "text", mask_for_output(texto or "")))
            self._store.salvar(conversa)  # terminal é mudo (invariável I4)
            return conversa

        resposta_llm = ""
        if midia is not None:
            conversa.historico.append(Mensagem("lead", midia[0], midia[1]))
            conversa.registrar_evento("message_in", {"media_type": midia[0], "marcador": midia[1]})
            transicao = transitar(conversa.estado, Evento.MIDIA)
        elif texto is not None:
            mascarada = mask_for_llm(texto)
            conversa.historico.append(Mensagem("lead", "text", mask_for_output(texto)))
            conversa.registrar_evento("message_in", {"texto": mask_for_output(texto)})
            evento, resposta_llm = self._classificar(conversa, mascarada)
            if evento is None:  # intent "outro": estado mantém, pede o que falta
                self._responder(conversa, (Efeito.PEDIR_FALTANTES,))
                self._store.salvar(conversa)
                return conversa
            transicao = transitar(
                conversa.estado, evento, fora_escopo_anterior=conversa.fora_escopo_anterior
            )
            if evento is Evento.FORA_DE_ESCOPO:
                conversa.fora_escopo_anterior = True
        else:
            raise ValueError("texto ou midia são obrigatórios")

        self._aplicar(conversa, transicao, resposta_llm)
        self._store.salvar(conversa)
        return conversa

    # ── classificação (LLM + guard) ──────────────────────────────────────
    def _classificar(
        self, conversa: Conversa, mensagem_mascarada: str
    ) -> tuple[Evento | None, str]:
        turno = self._llm.completar(
            estado=conversa.estado.value,
            dados=conversa.dados,
            historico=[m.texto for m in conversa.historico[-12:]],
            mensagem=mensagem_mascarada,
        )
        conversa.registrar_evento("intent_detected", {"intent": turno.intent})

        if self._guard_violado(conversa, turno.resposta):
            turno = self._llm.completar(
                estado=conversa.estado.value,
                dados=conversa.dados,
                historico=[m.texto for m in conversa.historico[-12:]],
                mensagem=mensagem_mascarada,
                aviso_correcao=True,
            )
            if self._guard_violado(conversa, turno.resposta):
                conversa.registrar_evento("price_guard_violation", {})
                turno.resposta = ""  # fallback canônico: o efeito fala

        if turno.campos is not None:
            conversa.dados = conversa.dados.merge(turno.campos)  # CORRIGE substitui (I3)

        return self._intent_para_evento(conversa, turno.intent), turno.resposta

    def _guard_violado(self, conversa: Conversa, resposta: str) -> bool:
        from app.domain.price_guard import validar_resposta

        return resposta != "" and not validar_resposta(resposta, conversa.cotacoes)

    def _intent_para_evento(self, conversa: Conversa, intent: str) -> Evento:
        if intent == "midia":
            return Evento.MIDIA
        if intent == "pede_humano":
            return Evento.PEDE_HUMANO
        if intent == "fora_de_escopo":
            return Evento.FORA_DE_ESCOPO
        if intent == "objecao_preco":
            return Evento.OBJECAO_PRECO
        if intent == "aceita":
            return Evento.ACEITA
        if intent == "rejeita":
            tem_cotacao = bool(conversa.cotacoes)
            if conversa.estado is Estado.COTACAO_APRESENTADA and not tem_cotacao:
                return Evento.REJEITA_APOS_RECUSA
            return Evento.REJEITA
        if intent == "contesta":
            return Evento.CONTESTA_RECUSA
        if intent == "confirma":
            motivo = conversa.dados.inelegivel()
            if motivo == "idade":
                return Evento.CONFIRMA_INELIGIVEL_IDADE
            if motivo == "veiculo":
                return Evento.CONFIRMA_INELIGIVEL_VEICULO
            return Evento.CONFIRMA
        if intent == "corrige":
            return Evento.CORRIGE
        if intent == "informa_dados":
            return (
                Evento.INFORMA_DADOS_COMPLETO
                if conversa.dados.completo()
                else Evento.INFORMA_DADOS_PARCIAL
            )
        return None  # intent "outro": sem transição — só pede o que falta (§6.2)

    # ── aplicação da transição + efeitos ─────────────────────────────────
    def _aplicar(self, conversa: Conversa, transicao, resposta_llm: str = "") -> None:
        conversa.estado = transicao.estado
        if resposta_llm and resposta_llm != "":
            # fala do LLM aprovada pelo price-guard — preferencial (spec §4.1)
            if transicao.handoff_motivo:
                self._registrar_handoff(conversa, transicao.handoff_motivo)
            self._responder_texto(conversa, resposta_llm)
            self._encerrar_se_terminal(conversa)
            return
        if transicao.handoff_motivo:
            self._registrar_handoff(conversa, transicao.handoff_motivo)
            if transicao.efeitos == ():
                self._responder_texto(conversa, self._texto_handoff(transicao.handoff_motivo))
                self._encerrar_se_terminal(conversa)
                return
        if Efeito.CHAMAR_COTACAO in transicao.efeitos:
            self._cotar(conversa)
            return
        self._responder(conversa, transicao.efeitos)
        self._encerrar_se_terminal(conversa)

    def _encerrar_se_terminal(self, conversa: Conversa) -> None:
        if conversa.estado.value.startswith("ENCERRADA"):
            desfecho = conversa.estado.value.replace("ENCERRADA_", "").lower()
            conversa.registrar_evento("conversation_ended", {"desfecho": desfecho})

    def _registrar_handoff(self, conversa: Conversa, motivo: str) -> None:
        conversa.handoff = {
            "id": ulid(),
            "motivo": motivo,
            "status": "pendente",
            "resumo": self._resumo_handoff(conversa),
        }
        conversa.registrar_evento("handoff_requested", {"motivo": motivo})

    # ── cotação via ACL (spec §2) ────────────────────────────────────────
    def _cotar(self, conversa: Conversa) -> None:
        from app.domain.ports import QuoteRefused, TransientQuoteError

        payload = {
            "plano_id": "essencial",
            "idade": conversa.dados.idade,
            "veiculo_ano": conversa.dados.veiculo_ano,
            "cep": conversa.dados.cep,
            **({"data_inicio": conversa.dados.data_inicio} if conversa.dados.data_inicio else {}),
        }
        conversa.registrar_evento("lead_qualified", {"campos": _chaveados(conversa.dados)})
        conversa.registrar_evento("quote_requested", {"plano_id": "essencial"})
        try:
            cotacao = self._acl.cotar(payload)  # type: ignore[attr-defined]
        except QuoteRefused as exc:
            evento = (
                Evento.QUOTE_RECUSADA_VEICULO
                if "eiculo" in exc.motivo or "carro" in exc.motivo.lower()
                else Evento.QUOTE_RECUSADA_IDADE
            )
            conversa.registrar_evento("quote_refused", {"motivo": exc.motivo})
            self._aplicar(conversa, transitar(conversa.estado, evento))
            return  # resposta canônica da recusa
        except TransientQuoteError:
            aberto = getattr(self._acl.breaker, "state", None)
            if aberto is not None and aberto.value == "open":
                conversa.circuito_reaberturas += 1
                if conversa.circuito_reaberturas >= 2:
                    self._aplicar(conversa, transitar(conversa.estado, Evento.CIRCUITO_REABERTO))
                    return
            conversa.retry_pending = True
            conversa.registrar_evento("quote_attempt_failed", {"reason": "transiente"})
            self._aplicar(conversa, transitar(conversa.estado, Evento.FALHA_PERSISTENTE))
            return
        cotacao["quote_id"] = ulid()
        conversa.cotacoes.append(cotacao)
        conversa.registrar_evento(
            "quote_succeeded", {"quote_id": cotacao["quote_id"], "premio": cotacao["premio_mensal"]}
        )
        self._aplicar(conversa, transitar(conversa.estado, Evento.QUOTE_OK))

    # ── efeitos → fala do Agente (catálogo — spec §6) ────────────────────
    def _responder(self, conversa: Conversa, efeitos) -> None:
        textos: list[str] = []
        for efeito in efeitos:
            texto = self._texto_do_efeito(conversa, efeito)
            if texto:
                textos.append(texto)
            if efeito is Efeito.AGENDAR_RETENTATIVA:
                conversa.registrar_evento("retry_scheduled", {})
        if not textos:
            textos = [t("agent.aguardando_humano_idempotente", self._cat)]
        conversa.historico.append(Mensagem("agente", "text", " ".join(textos)))
        conversa.registrar_evento("message_out", {"estado": conversa.estado.value})

    def _texto_do_efeito(self, conversa: Conversa, efeito: Efeito) -> str:
        dados = conversa.dados
        match efeito:
            case Efeito.SAUDAR_PEDIR_DADOS:
                return t("agent.saudacao", self._cat)
            case Efeito.PEDIR_FALTANTES:
                campo = dados.faltantes()[0] if dados.faltantes() else "veiculo_ano"
                chave = {"veiculo_ano": "veiculo", "idade": "idade", "cep": "cep"}[campo]
                return t(f"agent.pedir_campo.{chave}", self._cat)
            case Efeito.ECO_CONFIRMACAO:
                return t(
                    "agent.eco_confirmacao",
                    self._cat,
                    veiculo=dados.veiculo_texto or "",
                    idade=dados.idade or "",
                    cep=dados.cep or "",
                )
            case Efeito.PEDIR_TEXTO_MIDIA:
                return t("agent.midia_nao_suportada", self._cat, tipo_midia="este arquivo")
            case Efeito.RECUSAR_IDADE_LOCAL | Efeito.RECUSAR_EMPATICA_IDADE:
                return t("agent.recusa_idade", self._cat)
            case Efeito.RECUSAR_VEICULO_LOCAL | Efeito.RECUSAR_EMPATICA_VEICULO:
                return t("agent.recusa_veiculo", self._cat)
            case Efeito.MENSAGEM_FALHA_HONESTA:
                return t("agent.falha_tecnica_honesta", self._cat)
            case Efeito.APRESENTAR_COTACAO:
                return self._apresentar_cotacao(conversa)
            case Efeito.REBATER_OBJECAO:
                conversa.registrar_evento("objection_raised", {})
                return t("agent.objecao_rebatida_intro", self._cat) + " " + self._comparativo()
            case Efeito.REDIRECIONAR_ESCOPO:
                return t("agent.fora_escopo_redirect", self._cat)
            case Efeito.ENCERRAR_PERDIDO:
                return t("agent.encerramento_perdido", self._cat)
            case Efeito.MENSAGEM_IDEMPOTENTE_HUMANO:
                return t("agent.aguardando_humano_idempotente", self._cat)
            # efeitos não-textuais (CHAMAR_COTACAO é interceptado antes em _aplicar)
            case _:
                return ""

    def _apresentar_cotacao(self, conversa: Conversa) -> str:
        cot = conversa.cotacoes[-1]
        texto = t(
            "agent.cotacao_apresentacao_fallback",
            self._cat,
            plano_nome=cot.get("plano_nome", ""),
            premio=format_brl(cot["premio_mensal"]),
            franquia=format_brl(cot["franquia"]),
            coberturas=", ".join(cot.get("coberturas", [])),
            carencia_dias=cot.get("carencia", {}).get("dias", 30),
        )
        pro = cot.get("primeiro_pagamento_pro_rata")
        if pro:
            texto += " " + t(
                "agent.cotacao_prorata_linha",
                self._cat,
                valor_primeiro=format_brl(pro["valor_primeiro_pagamento"]),
                dias_cobrados=pro["dias_cobrados"],
            )
        conversa.registrar_evento("quote_presented", {"premio_mensal": cot["premio_mensal"]})
        return texto

    def _comparativo(self) -> str:
        """Rebate objeção com dados REAIS de /planos — só franquia/cobertura
        (prêmio por perfil não existe sem cotação — price-guard-safe)."""
        if self._planos is None:
            try:
                self._planos = self._acl.planos()  # type: ignore[attr-defined]
            except Exception:
                self._planos = []
        linhas = [
            f"{p['nome']}: franquia {format_brl(p['franquia'])}, cobre {', '.join(p['coberturas'])}"
            for p in self._planos
        ]
        return "; ".join(linhas) if linhas else ""

    # ── helpers ──────────────────────────────────────────────────────────
    def _texto_handoff(self, motivo: str) -> str:
        chave = {
            "aceite_fechamento": "agent.handoff_aceite",
            "preferencia_humana": "agent.handoff_humano_imediato",
            "falha_tecnica": "agent.handoff_falha_tecnica",
            "objecao_preco": "agent.handoff_objecao",
            "inelegivel_contestado": "agent.handoff_geral",
            "fora_escopo": "agent.handoff_fora_escopo",
        }[motivo]
        return t(chave, self._cat)

    def _responder_texto(self, conversa: Conversa, texto: str) -> None:
        conversa.historico.append(Mensagem("agente", "text", texto))
        conversa.registrar_evento("message_out", {"estado": conversa.estado.value})

    def _resumo_handoff(self, conversa: Conversa) -> str:
        dados = conversa.dados
        partes = [f"veículo {dados.veiculo_texto or '?'}"]
        if dados.idade:
            partes.append(f"{dados.idade} anos")
        if dados.cep:
            partes.append(f"CEP {mask_for_output(dados.cep)}")
        if conversa.cotacoes:
            partes.append(f"cotação {format_brl(conversa.cotacoes[-1]['premio_mensal'])}")
        return ", ".join(partes)[:500]


def _chaveados(dados: Campos) -> dict:
    return {
        "veiculo_texto": dados.veiculo_texto,
        "veiculo_ano": dados.veiculo_ano,
        "idade": dados.idade,
        "cep": mask_for_output(dados.cep) if dados.cep else None,
    }
