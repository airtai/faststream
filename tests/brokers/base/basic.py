from typing import Any, Dict, Tuple


class BaseTestcaseConfig:
    timeout: float = 3.0

    def get_subscriber_params(
        self, *args: Any, **kwargs: Any
    ) -> Tuple[
        Tuple[Any, ...],
        Dict[str, Any],
    ]:
        return args, kwargs
