-- UE4SS Twitch Chaos Mod

local UEHelpers = require("UEHelpers")  -- Load UEHelpers

-- Define the base path
local base_path = "./pyChaosMod/"

local ChaosBotVersion = "2.5.0"

local command_modules = {}

-- JSON encoding and decoding functions
-- Based on json.lua by rxi (https://github.com/rxi/json.lua)

local encode

local escape_char_map = {
  [ "\\" ] = "\\\\",
  [ "\"" ] = "\\\"",
  [ "\b" ] = "\\b",
  [ "\f" ] = "\\f",
  [ "\n" ] = "\\n",
  [ "\r" ] = "\\r",
  [ "\t" ] = "\\t",
}

local escape_char_map_inv = { [ "\\/" ] = "/" }
for k, v in pairs(escape_char_map) do
  escape_char_map_inv[v] = k
end

local function escape_char(c)
  return escape_char_map[c] or string.format("\\u%04x", c:byte())
end

local function encode_nil(val)
  return "null"
end

local function encode_table(val, stack)
  local res = {}
  stack = stack or {}

  -- Circular reference?
  if stack[val] then error("circular reference") end

  stack[val] = true

  if rawget(val, 1) ~= nil or next(val) == nil then
    -- Treat as array -- check keys are valid and it is not sparse
    local n = 0
    for k in pairs(val) do
      if type(k) ~= "number" then
        error("invalid table: mixed or invalid key types")
      end
      n = n + 1
    end
    if n ~= #val then
      error("invalid table: sparse array")
    end
    -- Encode
    for i, v in ipairs(val) do
      table.insert(res, encode(v, stack))
    end
    stack[val] = nil
    return "[" .. table.concat(res, ",") .. "]"

  else
    -- Treat as an object
    for k, v in pairs(val) do
      if type(k) ~= "string" then
        error("invalid table: mixed or invalid key types")
      end
      table.insert(res, encode(k, stack) .. ":" .. encode(v, stack))
    end
    stack[val] = nil
    return "{" .. table.concat(res, ",") .. "}"
  end
end

local function encode_string(val)
  return '"' .. val:gsub('[%z\1-\31\\"]', escape_char) .. '"'
end

local function encode_number(val)
  -- Check for NaN, -inf and inf
  if val ~= val or val <= -math.huge or val >= math.huge then
    error("unexpected number value '" .. tostring(val) .. "'")
  end
  return string.format("%.14g", val)
end

local type_func_map = {
  [ "nil"     ] = encode_nil,
  [ "table"   ] = encode_table,
  [ "string"  ] = encode_string,
  [ "number"  ] = encode_number,
  [ "boolean" ] = tostring,
}

encode = function(val, stack)
  local t = type(val)
  local f = type_func_map[t]
  if f then
    return f(val, stack)
  end
  error("unexpected type '" .. t .. "'")
end

function json_encode(val)
  return ( encode(val) )
end

-- Decoding functions

local parse

local function create_set(...)
  local res = {}
  for i = 1, select("#", ...) do
    res[ select(i, ...) ] = true
  end
  return res
end

local space_chars   = create_set(" ", "\t", "\r", "\n")
local delim_chars   = create_set(" ", "\t", "\r", "\n", "]", "}", ",")
local escape_chars  = create_set("\\", "/", '"', "b", "f", "n", "r", "t", "u")
local literals      = create_set("true", "false", "null")

local literal_map = {
  [ "true"  ] = true,
  [ "false" ] = false,
  [ "null"  ] = nil,
}

local function next_char(str, idx, set, negate)
  for i = idx, #str do
    if set[str:sub(i, i)] ~= negate then
      return i
    end
  end
  return #str + 1
end

local function decode_error(str, idx, msg)
  local line_count = 1
  local col_count = 1
  for i = 1, idx - 1 do
    col_count = col_count + 1
    if str:sub(i, i) == "\n" then
      line_count = line_count + 1
      col_count = 1
    end
  end
  error( string.format("%s at line %d col %d", msg, line_count, col_count) )
end

local function codepoint_to_utf8(n)
  -- http://scripts.sil.org/cms/scripts/page.php?site_id=nrsi&id=iws-appendixa
  local f = math.floor
  if n <= 0x7f then
    return string.char(n)
  elseif n <= 0x7ff then
    return string.char(f(n / 64) + 192, n % 64 + 128)
  elseif n <= 0xffff then
    return string.char(f(n / 4096) + 224, f(n % 4096 / 64) + 128, n % 64 + 128)
  elseif n <= 0x10ffff then
    return string.char(f(n / 262144) + 240, f(n % 262144 / 4096) + 128,
                       f(n % 4096 / 64) + 128, n % 64 + 128)
  end
  error( string.format("invalid unicode codepoint '%x'", n) )
end

local function parse_unicode_escape(s)
  local n1 = tonumber( s:sub(3, 6),  16 )
  local n2 = tonumber( s:sub(9, 12), 16 )
  -- Surrogate pair?
  if n2 then
    return codepoint_to_utf8((n1 - 0xd800) * 0x400 + (n2 - 0xdc00) + 0x10000)
  else
    return codepoint_to_utf8(n1)
  end
end

local function parse_string(str, i)
  local res = ""
  local j = i + 1
  local k = j

  while j <= #str do
    local x = str:byte(j)

    if x < 32 then
      decode_error(str, j, "control character in string")
    end

    if x == 92 then -- `\`: Escape
      if j ~= k then
        res = res .. str:sub(k, j - 1)
      end
      j = j + 1
      local c = str:sub(j, j)
      if c == "u" then
        local hex = str:match("^[dD][89aAbB]%x%x\\u%x%x%x%x", j + 1)
                 or str:match("^%x%x%x%x", j + 1)
                 or decode_error(str, j - 1, "invalid unicode escape in string")
        res = res .. parse_unicode_escape(hex)
        j = j + #hex
      else
        if not escape_chars[c] then
          decode_error(str, j - 1, "invalid escape char '" .. c .. "' in string")
        end
        res = res .. escape_char_map_inv[c]
      end
      k = j + 1
    elseif x == 34 then -- `"`: End of string
      res = res .. str:sub(k, j - 1)
      return res, j + 1
    end

    j = j + 1
  end

  decode_error(str, i, "expected closing quote for string")
end

local function parse_number(str, i)
  local x = next_char(str, i, delim_chars)
  local s = str:sub(i, x - 1)
  local n = tonumber(s)
  if not n then
    decode_error(str, i, "invalid number '" .. s .. "'")
  end
  return n, x
end

local function parse_literal(str, i)
  local x = next_char(str, i, delim_chars)
  local word = str:sub(i, x - 1)
  if not literals[word] then
    decode_error(str, i, "invalid literal '" .. word .. "'")
  end
  return literal_map[word], x
end

local function parse_array(str, i)
  local res = {}
  local n = 1
  i = i + 1
  while 1 do
    local x
    i = next_char(str, i, space_chars, true)
    -- Empty / end of array?
    if str:sub(i, i) == "]" then
      i = i + 1
      break
    end
    -- Read token
    x, i = parse(str, i)
    res[n] = x
    n = n + 1
    -- Next token
    i = next_char(str, i, space_chars, true)
    local chr = str:sub(i, i)
    i = i + 1
    if chr == "]" then break end
    if chr ~= "," then decode_error(str, i, "expected ']' or ','") end
  end
  return res, i
end

local function parse_object(str, i)
  local res = {}
  i = i + 1
  while 1 do
    local key, val
    i = next_char(str, i, space_chars, true)
    -- Empty / end of object?
    if str:sub(i, i) == "}" then
      i = i + 1
      break
    end
    -- Read key
    if str:sub(i, i) ~= '"' then
      decode_error(str, i, "expected string for key")
    end
    key, i = parse(str, i)
    -- Read ':' delimiter
    i = next_char(str, i, space_chars, true)
    if str:sub(i, i) ~= ":" then
      decode_error(str, i, "expected ':' after key")
    end
    i = next_char(str, i + 1, space_chars, true)
    -- Read value
    val, i = parse(str, i)
    -- Set
    res[key] = val
    -- Next token
    i = next_char(str, i, space_chars, true)
    local chr = str:sub(i, i)
    i = i + 1
    if chr == "}" then break end
    if chr ~= "," then decode_error(str, i, "expected '}' or ','") end
  end
  return res, i
end

local char_func_map = {
  [ '"' ] = parse_string,
  [ "0" ] = parse_number,
  [ "1" ] = parse_number,
  [ "2" ] = parse_number,
  [ "3" ] = parse_number,
  [ "4" ] = parse_number,
  [ "5" ] = parse_number,
  [ "6" ] = parse_number,
  [ "7" ] = parse_number,
  [ "8" ] = parse_number,
  [ "9" ] = parse_number,
  [ "-" ] = parse_number,
  [ "t" ] = parse_literal,
  [ "f" ] = parse_literal,
  [ "n" ] = parse_literal,
  [ "[" ] = parse_array,
  [ "{" ] = parse_object,
}

parse = function(str, idx)
  local chr = str:sub(idx, idx)
  local f = char_func_map[chr]
  if f then
    return f(str, idx)
  end
  decode_error(str, idx, "unexpected character '" .. chr .. "'")
end

function json_decode(str)
  if type(str) ~= "string" then
    error("expected argument of type string, got " .. type(str))
  end
  local res, idx = parse(str, next_char(str, 1, space_chars, true))
  idx = next_char(str, idx, space_chars, true)
  if idx <= #str then
    decode_error(str, idx, "trailing garbage")
  end
  return res
end






-- Function to load a command module
function load_command_module(command_name)
    if not command_modules[command_name] then
        local success, module = pcall(require, "commands." .. command_name)
        if success then
            command_modules[command_name] = module
        else
            print("[ChaosMod] Failed to load command module: " .. command_name)
            print("[ChaosMod] Error: " .. module)
            return nil
        end
    end
    return command_modules[command_name]
end

function ExecuteCommand(commandName)
    print("[ChaosMod] Executing command: " .. commandName)

    local module = load_command_module(commandName)
    if module and module.execute then
        ExecuteInGameThread(function()
            module.execute()
        end)
    else
        print("[ChaosMod] Failed to execute command: " .. commandName)
    end
end



-- Function to download and extract ChaosBot
function downloadAndExtractChaosBot(base_path)
    local findUI = FindFirstOf("menuChaos_C")
    if findUI:IsValid() then
        findUI:downloadStarted()
    end
    
    local zipUrl = "https://github.com/modestimpala/VotVChaosMod/releases/download/latest/ChaosBot.zip"
    local zipPath = base_path .. "ChaosBot.zip"
    local logPath = base_path .. "download_log.txt"
    
    -- Download the zip file
    print("[ChaosMod] Attempting to download ChaosBot")
    local downloadCommand = string.format(
        'powershell -command "&{$ProgressPreference = \'SilentlyContinue\'; ' ..
        '$ErrorActionPreference = \'Stop\'; ' ..
        'try { ' ..
        '(New-Object Net.WebClient).DownloadFile(\'%s\', \'%s\'); ' ..
        '\'Download successful\' ' ..
        '} catch { ' ..
        '$_.Exception.Message ' ..
        '} }" > "%s" 2>&1',
        zipUrl, zipPath, logPath
    )
    local downloadSuccess = os.execute(downloadCommand)
    
    -- Read and print the log
    local logFile = io.open(logPath, "r")
    if logFile then
        local logContent = logFile:read("*all")
        print("[ChaosMod] Download log:")
        print(logContent)
        logFile:close()
    else
        print("[ChaosMod] Failed to read download log")
    end
    
    if not downloadSuccess then
        print("[ChaosMod] Failed to download ChaosBot")
        return false
    end
    
    -- Extract the zip file
    print("[ChaosMod] Attempting to extract ChaosBot")
    local extractCommand = string.format(
        'powershell -command "&{$ProgressPreference = \'SilentlyContinue\'; ' ..
        '$ErrorActionPreference = \'Stop\'; ' ..
        'try { ' ..
        'Expand-Archive -Path \'%s\' -DestinationPath \'%s\' -Force; ' ..
        '\'Extraction successful\' ' ..
        '} catch { ' ..
        '$_.Exception.Message ' ..
        '} }" >> "%s" 2>&1',
        zipPath, base_path, logPath
    )
    local extractSuccess = os.execute(extractCommand)
    
    -- Read and print the updated log
    logFile = io.open(logPath, "r")
    if logFile then
        local logContent = logFile:read("*all")
        print("[ChaosMod] Updated log (including extraction):")
        print(logContent)
        logFile:close()
    else
        print("[ChaosMod] Failed to read updated log")
    end
    
    if not extractSuccess then
        print("[ChaosMod] Failed to extract zip file")
        os.remove(zipPath)
        return false
    end
    
    -- Clean up the zip file
    os.remove(zipPath)
    return true
end

function beginDownload(base_path, exePath)
    if downloadAndExtractChaosBot(base_path) then
        print("[ChaosMod] Attempting to launch newly downloaded executable")
        local success, err, code = os.execute(string.format('start "" "%s"', exePath))
        
        if success then
            print("[ChaosMod] Executable opened successfully after download: " .. exePath)
        else
            print("[ChaosMod] Failed to open executable after download: " .. (err or "Unknown error"))
            local findUI = FindFirstOf("menuChaos_C")
            if findUI:IsValid() then
                findUI:launchBotFailed()
            end
        end
    else
        local findUI = FindFirstOf("menuChaos_C")
        if findUI:IsValid() then
            findUI:downloadFailed()
        end
        print("[ChaosMod] Failed to download and extract ChaosBot")
    end
end

function launchChaosBot()
    -- Ensure base_path directory exists
    local createDirCommand = string.format('if not exist "%s" mkdir "%s"', base_path, base_path)
    if not os.execute(createDirCommand) then
        print("[ChaosMod] Failed to create directory: " .. base_path)
        return
    end

    local exePath = base_path .. "ChaosBot.exe"
    local scriptPath = base_path .. "ChaosBot.py"
    local updaterFile = base_path .. "ChaosBot_Updater.exe"

    -- Check if executable exists
    local exeFile = io.open(exePath, "r")
    if exeFile then
        exeFile:close() 
        -- Check if updater exists
        if not io.open(updaterFile, "r") then
            print("[ChaosMod] Updater not found. Downloading executable...")
            beginDownload(base_path, exePath)
        end

        -- Launch executable
        print("[ChaosMod] Attempting to launch executable: " .. exePath)
        local psCmd = string.format('powershell.exe -Command "Start-Process -FilePath \'%s\' -Verb RunAs"', exePath)
        local success, err, code = os.execute(psCmd)
        if success then
            print("[ChaosMod] Executable opened successfully: " .. exePath)
        else
            print("[ChaosMod] Failed to open executable: " .. (err or "Unknown error"))
        end
    else
        -- Executable not found, check for Python script
        if io.open(scriptPath, "r") then
            print("[ChaosMod] Executable not found. Trying to open with Python")
            local success, err, code = os.execute(string.format('start "" python "%s"', scriptPath))
            if success then
                print("[ChaosMod] Python script opened successfully: " .. scriptPath)
            else
                print("[ChaosMod] Failed to open Python script: " .. (err or "Unknown error"))
                print("[ChaosMod] Downloading executable...")
                beginDownload(base_path, exePath)
            end
        else
            -- Neither executable nor Python script found
            print("[ChaosMod] Both executable and Python script not found")
            print("[ChaosMod] Downloading executable...")
            beginDownload(base_path, exePath)
        end
    end
end



RegisterConsoleCommandHandler(("Chaos"), function(full, args)
    local command = args[1]
    ExecuteCommand(command)
    return true
end)

-- Console Commands
RegisterConsoleCommandHandler(("launchChaosBot"), function(full, args)
    launchChaosBot()
    return true
end)




print("[ChaosMod] Successfully loaded ChaosMod")





-- Moddy 2024
-- Licensed under Creative Commons Attribution 4.0 International License