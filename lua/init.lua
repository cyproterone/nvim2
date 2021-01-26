return function(args)
  local cwd = unpack(args)

  local uv = vim.loop
  local on_exit = function(code)
    vim.schedule(
      function()
        vim.api.nvim_err_writeln(" | EXITED - " .. code)
      end
    )
  end
  local on_stdout = function(data)
    vim.schedule(
      function()
        vim.api.nvim_out_write(data)
      end
    )
  end
  local on_stderr = function(data)
    vim.schedule(
      function()
        vim.api.nvim_err_write(data)
      end
    )
  end
  local spawn = function(prog, args, input, cwd, env, handlers)
    local _env = {}
    for key, val in pairs(vim.api.nvim_call_function("environ", {})) do
      table.insert(_env, {key, val})
    end
    local stdin = uv.new_pipe(false)
    local stdout = uv.new_pipe(false)
    local stderr = uv.new_pipe(false)
    local opts = {
      stdio = {stdin, stdout, stderr},
      args = args,
      cwd = cwd
      -- env = _env
    }

    local process, pid = nil, nil
    process, pid =
      uv.spawn(
      prog,
      opts,
      function(code, signal)
        local handles = {stdin, stdout, stderr, process}
        for _, handle in ipairs(handles) do
          uv.close(handle)
        end
        (handlers.on_exit or on_exit)(code)
      end
    )
    assert(process, pid)

    uv.read_start(
      stdout,
      function(err, data)
        assert(not err, err)
        if data then
          (handlers.on_stdout or on_stderr)(data)
        end
      end
    )

    uv.read_start(
      stderr,
      function(err, data)
        assert(not err, err)
        if data then
          (handlers.on_stderr or on_stdout)(data)
        end
      end
    )

    if input then
      uv.write(
        stdin,
        input,
        function(err)
          assert(not err, err)
          uv.shutdown(
            stdin,
            function(err)
              assert(not err, err)
            end
          )
        end
      )
    end

    return pid
  end

  local handlers = {
    on_exit = on_exit,
    on_stdout = on_stdout,
    on_stderr = on_stderr
  }

  --
  --
  --
  -- DOMAIN CODE
  --
  --

  local VENV = cwd .. "/.vars/runtime"
  local PATH = VENV .. "/bin:" .. vim.api.nvim_call_function("getenv", {"PATH"})
  local env = {PATH = PATH, VIRTUAL_ENV = VENV}

  local args = {
    "-m",
    "python",
    "run",
    "--socket",
    vim.api.nvim_get_vvar("servername")
  }
  spawn("python3", args, nil, cwd, env, handlers)
end
