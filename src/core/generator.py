from __future__ import annotations

from dataclasses import dataclass

from core.clash_builder import build_clash_config, dump_clash_yaml
from core.parser import parse_node, split_subscription_lines


class GenerationError(RuntimeError):
    pass


@dataclass(slots=True)
class GenerationResult:
    node_count: int
    config: dict[str, object]
    yaml_text: str


def generate_from_subscription_body(
    body: str,
    *,
    port: int = 1082,
    allow_lan: bool = True,
) -> GenerationResult:
    nodes = [node for line in split_subscription_lines(body) if (node := parse_node(line))]
    if not nodes:
        raise GenerationError("解析结果为空")
    config = build_clash_config(nodes, port=port, allow_lan=allow_lan)
    yaml_text = dump_clash_yaml(config)
    return GenerationResult(node_count=len(nodes), config=config, yaml_text=yaml_text)
