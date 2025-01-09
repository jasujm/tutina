import contextlib
import functools
from typing import TYPE_CHECKING, Any, AsyncIterator, Awaitable, Callable

if TYPE_CHECKING:
    import fastapi


PreloadFunction = Callable[[], contextlib.AbstractAsyncContextManager[Any]]


class PreloadedDependencies:
    def __init__(self) -> None:
        self._exit_stack = contextlib.AsyncExitStack()
        self._dependencies: list[PreloadFunction] = []
        self._cache: dict[PreloadFunction, Any] = {}

    def register(self, func: PreloadFunction) -> Callable[[], Any]:
        self._dependencies.append(func)

        @functools.wraps(func)
        def _func_from_cache():
            return self._cache[func]

        return _func_from_cache

    @contextlib.asynccontextmanager
    async def preload(self, _app: "fastapi.FastAPI") -> AsyncIterator[None]:
        async with self._exit_stack:
            for dependency in self._dependencies:
                self._cache[dependency] = await self._exit_stack.enter_async_context(
                    dependency()
                )
            yield
