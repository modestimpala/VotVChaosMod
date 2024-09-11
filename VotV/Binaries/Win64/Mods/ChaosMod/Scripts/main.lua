-- UE4SS Twitch Chaos Mod (using separate configs)

local json = require("json")  -- Load JSON library
local commands = require("commands")  -- Load commands 
local UEHelpers = require("UEHelpers")  -- Load UEHelpers

-- Define the base path
local base_path = "./pyChaosMod/"
local config_file = base_path .. "config.json"
local emails_master_file = base_path .. "emails_master.json"
local shops_master_file = base_path .. "shops_master.json"

local setupCorrect = false
local f = io.open(config_file, "r")
if f then 
    f:close()
    setupCorrect = true
end

if not setupCorrect then
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

if setupCorrect then
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

    -- Remove enable and result files if they exist
    os.remove(config.files.enable)
    os.remove(config.files.result)
    os.remove(config.files.emails_enable)
    local chaosEnabled = false
    local lastExecutedVersion = 0
    local emailsEnabled = false
    local lastShopOrder = 0

    RegisterConsoleCommandHandler(("Chaos"), function(full, args)
        local command = args[1]
        for _, cmd in ipairs(commands_config.commands) do
            if cmd.command == command then
                ExecuteCommand(cmd.command)
            end
        end
        return true
    end)

    -- Function to read the master JSON file
    local function readMasterFile(filepath)
        local file = io.open(filepath, "r")
        if not file then return {} end
        local content = file:read("*all")
        file:close()
        return json.decode(content) or {}
    end
    
    -- Function to write the master JSON file
    local function writeMasterFile(filepath, data)
        local file = io.open(filepath, "w")
        file:write(json.encode(data))
        file:close()
    end

    -- Function to process new emails
    local function processNewEmails()
        local emails = readMasterFile(emails_master_file)
        local processed = {}
        for i, email in ipairs(emails) do
            if not email.processed then
                local emailHandler = FindFirstOf("emailHandler_C")
                if not emailHandler:IsValid() then
                    local World = UEHelpers:GetWorld()
                    local emailHandler_C = StaticFindObject("/Game/Mods/ChaosMod/Assets/emailHandler.emailHandler_C")
                    emailHandler = World:SpawnActor(emailHandler_C, {}, {})
                end
                if emailHandler and emailHandler:IsValid() then
                    local fullBody = email.body .. " - " .. email.username
                    emailHandler:addTwitchEmail(FText(email.subject), FText(fullBody))
                end
                email.processed = true
                processed[#processed + 1] = i
            end
        end
        if #processed > 0 then
            writeMasterFile(emails_master_file, emails)
        end
    end

    local function processNewShopOrders()
        local orders = readMasterFile(shops_master_file)
        local processed = {}
        for i, order in ipairs(orders) do
            if not order.processed then
                local shopHandler = FindFirstOf("shopOrderHandler_C")
                if not shopHandler:IsValid() then
                    local World = UEHelpers:GetWorld()
                    local shopHandler_C = StaticFindObject("/Game/Mods/ChaosMod/Assets/shopOrderHandler.shopOrderHandler_C")
                    shopHandler = World:SpawnActor(shopHandler_C, {}, {})
                end
                if shopHandler and shopHandler:IsValid() then
                    shopHandler:placeOrderTwitch(FName(order.item), FText(order.username))
                end
                order.processed = true
                processed[#processed + 1] = i
            end
        end
        if #processed > 0 then
            writeMasterFile(shops_master_file, orders)
        end
    end

    -- Toggle chaos mod
    local function toggleChaosMod()
        chaosEnabled = not chaosEnabled
        if chaosEnabled then
            local file = io.open(config.files.enable, "w")
            file:write("true")
            file:close()
        else
            os.remove(config.files.enable)
        end
    end

    -- Manually trigger voting
    local function triggerVoting()
        if chaosEnabled then
            local file = io.open(config.files.vote_trigger, "w")
            file:write("trigger")
            file:close()
        end
    end

    -- Check for voting result
    local function checkVotingResult()
        local file = io.open(config.files.result, "r")
        if file and chaosEnabled then
            local content = file:read("*all")
            file:close()
        
            local result = json.decode(content)
            if result and result.version > lastExecutedVersion then
                lastExecutedVersion = result.version
                
                -- Split the command string in case it's a combined command
                local commandNames = {}
                for name in result.command:gmatch("[^;]+") do
                    -- Remove leading and trailing whitespace
                    name = name:match("^%s*(.-)%s*$")
                    table.insert(commandNames, name)
                end
                
                local commands = {}
                for _, name in ipairs(commandNames) do
                    for _, command in ipairs(commands_config.commands) do
                        if command.command == name then
                            table.insert(commands, command)
                            break
                        end
                    end
                end
                
                if #commands > 0 then
                    for _, command in ipairs(commands) do
                        ExecuteCommand(command.command)
                    end
                end
            end
        end
    end

    local function clearEvents()
        local mainGamemode_C = FindFirstOf("mainGamemode_C")
        if mainGamemode_C:IsValid() then
            mainGamemode_C.eventsActive:Empty()
            Hint("You can now pause/save")
        end
    end

    local function toggleEmails()
        emailsEnabled = not emailsEnabled
        if emailsEnabled then
            local file = io.open(config.files.emails_enable, "w")
            file:write("true")
            file:close()
            Hint("Twitch Emails enabled")
            LoopAsync(1000, function()
                if not emailsEnabled then
                    return true
                end
                ExecuteInGameThread(function() 
                    processNewEmails()
                end)
            end)
        else
            os.remove(config.files.emails_enable)
            local emailHandler = FindFirstOf("emailHandler_C")
            if emailHandler:IsValid() then
                emailHandler:K2_DestroyActor()
            end
            Hint("Twitch Emails disabled")
        end
    end

    -- Keybind hooks
    RegisterKeyBind(Key.F8, function() toggleChaosMod() end)
    RegisterKeyBind(Key.F7, function() triggerVoting() end)
    RegisterKeyBind(Key.F6, function() clearEvents() end)
    if config.emails.enabled then
        RegisterKeyBind(Key.F3, function() toggleEmails() end)
    end

    -- Main loop using loopasync
    LoopAsync(math.floor(config.update_interval * 1000), function()
        checkVotingResult()
        if config.chatShop.enabled then
            processNewShopOrders()
        end
    end)

    ExecuteWithDelay(5000, function()
        RegisterHook("/Script/Engine.PlayerController:ClientRestart", function(Context, NewPawn)
            os.remove(config.files.emails_enable)
            local emailHandler = FindFirstOf("emailHandler_C")
            if emailHandler:IsValid() then
                emailHandler:K2_DestroyActor()
            end
            os.remove(config.files.enable)

        end)
    end)

    print("[ChaosMod] Successfully loaded ChaosMod")
end