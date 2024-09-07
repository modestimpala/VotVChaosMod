local json = require("json")  -- Load JSON library
local UEHelpers = require("UEHelpers")  -- Load UEHelpers

-- Define the base path
local base_path = "./pyChaosMod/"
local config_file = base_path .. "config.json"

local setupCorrect = false
local f = io.open(config_file, "r")
if f then 
    f:close()
    print("[ChaosMod] Found config file")
    setupCorrect = true
end

if not setupCorrect then
    print("You do not have ChaosMod installed correctly. Please follow the instructions in the README.md")
    LoopAsync(10000, function()
        local notInstalled = FindFirstOf("chaosNotInstalledCorrectly_C")
        if not notInstalled:IsValid() then
            local World = UEHelpers:GetWorld()
            local obj = StaticFindObject("/Game/Mods/ChaosMod/Assets/chaosNotInstalledCorrectly.chaosNotInstalledCorrectly_C")
            notInstalled = World:SpawnActor(obj, {}, {})
        end
    end)
    return
end

-- Load configurations
local config_file = io.open(config_file, "r")
local config = json.decode(config_file:read("*all"))
config_file:close()

-- Prepend base_path to all file paths in config
for key, value in pairs(config.files) do
    config.files[key] = base_path .. value
end

local commands_file = io.open(config.files.commands, "r")
local commands_config = json.decode(commands_file:read("*all"))
commands_file:close()

local command_modules = {}

function Hint(text)
    local ui = FindFirstOf("umg_UI_C")
    if ui:IsValid() then
        ui:addHint(FText(text))
    else 
        print("[MyLuaMod] Failed to find UI")
    end
end

-- Function to load a command module
function load_command_module(command_name)
    if not command_modules[command_name] then
        local success, module = pcall(require, "commands." .. command_name)
        if success then
            command_modules[command_name] = module
        else
            print("Failed to load command module: " .. command_name)
            print("Error: " .. module)
            return nil
        end
    end
    return command_modules[command_name]
end

function ExecuteCommand(commandName)
    print("Executing command: " .. commandName)
    local command = nil
    for _, cmd in ipairs(commands_config.commands) do
        if cmd.command == commandName then
            command = cmd
            break
        end
    end

    if not command then
        print("Command not found: " .. commandName)
        return
    end

    local module = load_command_module(command.command)
    if module and module.execute then
        ExecuteInGameThread(function()
            module.execute()
            Hint(command.trigger_text)
        end)
    else
        print("Failed to execute command: " .. command.command)
    end
end

-- Rest of your script...