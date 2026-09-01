# Log de Execução Completa — C1 (entregável do desafio)

> Gerado em 2026-09-01T17:00:12 contra os CONTAINERS
> (`docker compose up` — agent-api :8001 · quote-api :8000 · postgres), com o legado
> instável real. correlation_id da execução: c1-final-0001.

# Conversa 01M1F8XGCYAPCT8Y5ESM2P36HT

**Agente**: Oi! Que bom te ver por aqui. Pra cotar seu seguro eu preciso de três coisas: o veículo com o ano, a sua idade e o CEP de onde o carro dorme.

**Lead**: oi, quero cotar um seguro

**Agente**: Qual a marca, modelo e ano do seu carro?

**Lead**: Onix 2022, tenho 30 anos e o CEP é 01***-***

**Agente**: Confirmando: veículo Onix 2022, 30 anos, CEP 01310-100. É isso?

**Lead**: é isso

**Agente**: Saiu a cotação! Plano Essencial: R$ 119,90/mês, franquia de R$ 4.500,00, cobrindo colisao, roubo, furto. Roubo e furto passam a valer após 30 dias de carência.

**Lead**: fechado!

**Agente**: Fechado! 🎉 Vou passar pra um vendedor finalizar a emissão da apólice. Já já te chamam.

## Eventos
- `1` **conversation_started** {}
- `2` **message_out** {'estado': 'QUALIFICANDO'}
- `3` **message_in** {'texto': 'oi, quero cotar um seguro'}
- `4` **intent_detected** {'intent': 'outro'}
- `5` **message_out** {'estado': 'QUALIFICANDO'}
- `6` **message_in** {'texto': 'Onix 2022, tenho 30 anos e o CEP é 01***-***'}
- `7` **intent_detected** {'intent': 'informa_dados'}
- `8` **message_out** {'estado': 'CONFIRMANDO'}
- `9` **message_in** {'texto': 'é isso'}
- `10` **intent_detected** {'intent': 'confirma'}
- `11` **lead_qualified** {'campos': {'veiculo_texto': 'Onix 2022', 'veiculo_ano': 2022, 'idade': 30, 'cep': '01***-***'}}
- `12` **quote_requested** {'plano_id': 'essencial'}
- `13` **quote_succeeded** {'quote_id': '01M1F8XKY0PNFM7R0T8MRCY2N9', 'premio': 119.9}
- `14` **quote_presented** {'premio_mensal': 119.9}
- `15` **message_out** {'estado': 'COTACAO_APRESENTADA'}
- `16` **message_in** {'texto': 'fechado!'}
- `17` **intent_detected** {'intent': 'aceita'}
- `18` **handoff_requested** {'motivo': 'aceite_fechamento'}
- `19` **message_out** {'estado': 'HANDOFF'}

> Handoff: **aceite_fechamento**

código da sessão: c1-final-0001