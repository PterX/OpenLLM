from __future__ import annotations

import asyncio, time, typing, os
import httpx, openai

from openai.types.chat import ChatCompletionAssistantMessageParam, ChatCompletionUserMessageParam
from openllm.common import (
  BentoInfo,
  EnvVars,
  async_run_command,
  output,
  run_command,
  stream_command_output,
)
from openllm.venv import ensure_venv

if typing.TYPE_CHECKING:
  from openai.types.chat import ChatCompletionMessageParam


def prep_env_vars(bento: BentoInfo) -> None:
  env_vars = bento.envs
  for env_var in env_vars:
    if not env_var.get('value'):
      continue
    key = env_var['name']
    value = env_var['value']
    os.environ[key] = value


def _get_serve_cmd(
  bento: BentoInfo, port: int = 3000, cli_args: typing.Optional[list[str]] = None
) -> tuple[list[str], EnvVars]:
  cmd = ['bentoml', 'serve', bento.bentoml_tag]
  if port != 3000:
    cmd += ['--port', str(port)]

  # Add CLI arguments if provided
  if cli_args:
    for arg in cli_args:
      cmd += ['--arg', arg]

  return cmd, EnvVars({'BENTOML_HOME': f'{bento.repo.path}/bentoml'})


def serve(
  bento: BentoInfo,
  port: int = 3000,
  cli_envs: typing.Optional[list[str]] = None,
  cli_args: typing.Optional[list[str]] = None,
) -> None:
  prep_env_vars(bento)
  cmd, env = _get_serve_cmd(bento, port=port, cli_args=cli_args)

  # Add CLI environment variables if provided
  if cli_envs:
    for env_var in cli_envs:
      if '=' in env_var:
        key, value = env_var.split('=', 1)
        env[key] = value
      else:
        env[env_var] = os.environ.get(env_var, '')

  venv = ensure_venv(bento, runtime_envs=env)
  output(f'Access the Chat UI at http://localhost:{port}/chat (or with you IP)')
  run_command(cmd, env=env, cwd=None, venv=venv)


async def _run_model(
  bento: BentoInfo,
  port: int = 3000,
  timeout: int = 600,
  cli_env: typing.Optional[dict[str, typing.Any]] = None,
  cli_args: typing.Optional[list[str]] = None,
) -> None:
  cmd, env = _get_serve_cmd(bento, port, cli_args=cli_args)

  # Merge cli environment variables if provided
  if cli_env:
    env.update(cli_env)

  venv = ensure_venv(bento, runtime_envs=env)
  async with async_run_command(cmd, env=env, cwd=None, venv=venv, silent=False) as server_proc:
    output(f'Model server started {server_proc.pid}')

    stdout_streamer = None
    stderr_streamer = None
    start_time = time.time()

    output('Model loading...', style='green')
    for _ in range(timeout):
      try:
        resp = httpx.get(f'http://localhost:{port}/readyz', timeout=3)
        if resp.status_code == 200:
          break
      except httpx.RequestError:
        if time.time() - start_time > 30:
          if not stdout_streamer:
            stdout_streamer = asyncio.create_task(
              stream_command_output(server_proc.stdout, style='gray')
            )
          if not stderr_streamer:
            stderr_streamer = asyncio.create_task(
              stream_command_output(server_proc.stderr, style='#BD2D0F')
            )
        await asyncio.sleep(1)
    else:
      output('Model failed to load', style='red')
      server_proc.terminate()
      return

    if stdout_streamer:
      stdout_streamer.cancel()
    if stderr_streamer:
      stderr_streamer.cancel()

    output('Model is ready', style='green')
    messages: list[ChatCompletionMessageParam] = []

    client = openai.AsyncOpenAI(base_url=f'http://localhost:{port}/v1', api_key='local')
    while True:
      try:
        message = input('user: ')
        if message == '':
          output('empty message, please enter something', style='yellow')
          continue
        messages.append(ChatCompletionUserMessageParam(role='user', content=message))
        output('assistant: ', end='', style='lightgreen')
        assistant_message = ''
        stream = await client.chat.completions.create(
          model=(await client.models.list()).data[0].id, messages=messages, stream=True
        )
        async for chunk in stream:
          text = chunk.choices[0].delta.content or ''
          assistant_message += text
          output(text, end='', style='lightgreen')
        messages.append(
          ChatCompletionAssistantMessageParam(role='assistant', content=assistant_message)
        )
        output('')
      except KeyboardInterrupt:
        break
    output('\nStopping model server...', style='green')
    output('Stopped model server', style='green')


def run(
  bento: BentoInfo,
  port: int = 3000,
  timeout: int = 600,
  cli_envs: typing.Optional[list[str]] = None,
  cli_args: typing.Optional[list[str]] = None,
) -> None:
  prep_env_vars(bento)

  # Add CLI environment variables to the process
  env = {}
  if cli_envs:
    for env_var in cli_envs:
      if '=' in env_var:
        key, value = env_var.split('=', 1)
        env[key] = value
      else:
        env[env_var] = os.environ.get(env_var, '')

  asyncio.run(_run_model(bento, port=port, timeout=timeout, cli_env=env, cli_args=cli_args))
