local json = require("json")  -- Load JSON library
local UEHelpers = require("UEHelpers")  -- Load UEHelpers

-- Define the base paths
local base_path = "./pyChaosMod/"

-- Function to read config files
local function readConfig(filename)
    local config = {}
    local file = io.open(base_path .. filename, "r")
    if file then
        for line in file:lines() do
            local key, value = line:match("([^=]+)=(.+)")
            if key and value then
                key = key:gsub("%s+", "")
                value = value:gsub("%s+", "")
                if value == "true" then
                    config[key] = true
                elseif value == "false" then
                    config[key] = false
                elseif tonumber(value) then
                    config[key] = tonumber(value)
                else
                    config[key] = value
                end
            end
        end
        file:close()
    end
    return config
end

-- Check if setup is correct
local setupCorrect = io.open(base_path .. "chatShop.cfg", "r") ~= nil

if setupCorrect then
    print("[ChaosMod] Found config files")
else
    print("[ChaosMod] Config files not found")
    return
end

-- Load configurations
local config = {
    chatShop = readConfig("chatShop.cfg"),
    emails = readConfig("emails.cfg"),
    twitch = readConfig("twitch.cfg"),
    voting = readConfig("voting.cfg")
}

-- Define file paths
config.files = {
    enable = base_path .. "enable.txt",
    emails_enable = base_path .. "emails_enable",
    emails_master = base_path .. "emails_master.json",
    shops_master = base_path .. "shops_master.json"
}

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

    local module = load_command_module(commandName)
    if module and module.execute then
        ExecuteInGameThread(function()
            module.execute()
        end)
    else
        print("Failed to execute command: " .. commandName)
    end
end

-- Moddy 2024
-- Licensed under Creative Commons Attribution 4.0 International License