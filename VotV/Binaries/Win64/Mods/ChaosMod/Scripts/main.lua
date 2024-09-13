-- UE4SS Twitch Chaos Mod

local json = require("json")  -- Load JSON library
local commands = require("commands")  -- Load commands 
local utils = require("utils")  -- Load utils
local UEHelpers = require("UEHelpers")  -- Load UEHelpers

-- Define the base path
local base_path = "./pyChaosMod/"


-- Read configurations
local config = {
    chatShop = readConfig("chatShop.cfg"),
    emails = readConfig("emails.cfg"),
    twitch = readConfig("twitch.cfg"),
    voting = readConfig("voting.cfg")
}

-- Define file paths
config.files = {
    enable = base_path .. "enable.txt",
    emails_enable = base_path .. "emails_enable.txt",
    emails_master = base_path .. "emails_master.json",
    shops_master = base_path .. "shops_master.json",
    votes = base_path .. "votes.txt",
    voting_enabled = base_path .. "voting_enabled.txt",
    shopOpen = base_path .. "shopOpen.txt"
}

-- Wipe master file contents if they exist
if io.open(config.files.shops_master, "r") then
    safeWriteToFile(config.files.shops_master, "[]")
else
    print("shops_master file does not exist")
end

if io.open(config.files.emails_master, "r") then
    safeWriteToFile(config.files.emails_master, "[]")
else
    print("emails_master file does not exist")
end

-- Wipe votes if the file exists
if io.open(config.files.votes, "r") then
    safeWriteToFile(config.files.votes, " ")
else
    print("votes file does not exist")
end

-- Close shop if the file exists
if io.open(config.files.shopOpen, "r") then
    safeWriteToFile(config.files.shopOpen, "false")
else
    print("shopOpen file does not exist")
end

-- Remove enable and result files if they exist
safeRemoveFile(config.files.enable)
safeRemoveFile(config.files.emails_enable)
safeRemoveFile(config.files.voting_enabled)

local chaosEnabled = false
local emailsEnabled = false
local isShopOpen = false

RegisterConsoleCommandHandler(("Chaos"), function(full, args)
    local command = args[1]
    ExecuteCommand(command)
    return true
end)

-- Function to process new emails
local function processNewEmails()
    local emails = readMasterFile(config.files.emails_master)
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
        writeMasterFile(config.files.emails_master, emails)
    end
end

-- Function to process new shop orders
local function processNewShopOrders()
    local orders = readMasterFile(config.files.shops_master)
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
        writeMasterFile(config.files.shops_master, orders)
    end
end

-- Toggle chaos mod
local function toggleChaosMod()
    chaosEnabled = not chaosEnabled
    ExecuteInGameThread(function()
        local findConstructor = FindFirstOf("chaosConstructor_C")
        local findWindow = FindFirstOf("votingMenu_C")
        if chaosEnabled then
            if not findConstructor:IsValid() and not findWindow:IsValid() then
                local World = UEHelpers:GetWorld()
                local obj = StaticFindObject("/Game/Mods/ChaosMod/Assets/Widgets/chaosConstructor.chaosConstructor_C")
                local spawned = World:SpawnActor(obj, {}, {})
            end

            if findWindow:IsValid() then
                findWindow:enableMenu()
                -- findWindow:resetState()
            end

            local file = io.open(config.files.enable, "w")
            file:write("true")
            file:close()
            print("ChaosMod enabled")
        else
            if findConstructor:IsValid() then
                findConstructor:K2_DestroyActor()
            end
            local findWindow = FindFirstOf("votingMenu_C")
            if findWindow:IsValid() then
                findWindow:disableMenu()
            end
            os.remove(config.files.enable)
            print("ChaosMod disabled")
        end
    end)
end

local function disableChaosMod()
    chaosEnabled = false
    ExecuteInGameThread(function()
        local findConstructor = FindFirstOf("chaosConstructor_C")
        local findWindow = FindFirstOf("votingMenu_C")
        if findConstructor:IsValid() then
            findConstructor:K2_DestroyActor()
        end
        if findWindow:IsValid() then
            findWindow:disableMenu()
        end
    end)
    os.remove(config.files.enable)
    print("ChaosMod disabled")
end

-- Manually trigger voting
local function triggerVoting()
    if chaosEnabled then
        local findWindow = FindFirstOf("votingMenu_C")
        if findWindow:IsValid() then
            ExecuteInGameThread(function()
                findWindow:startVote()
            end)
        end
    end
end

-- Clear events
local function clearEvents()
    local mainGamemode_C = FindFirstOf("mainGamemode_C")
    if mainGamemode_C:IsValid() then
        ExecuteInGameThread(function()
            mainGamemode_C.eventsActive:Empty()
        end)
        Hint("You can now pause/save")
    end
end

-- Toggle emails
local function toggleEmails()
    emailsEnabled = not emailsEnabled
    
    local findWindow = FindFirstOf("votingMenu_C")
    if findWindow:IsValid() then
        ExecuteInGameThread(function()
            findWindow:toggleEmails()
        end)
    end


    if emailsEnabled then
        local file = io.open(config.files.emails_enable, "w")
        file:write("true")
        file:close()
        Hint("Twitch Emails enabled")
        LoopAsync(1000, function()
            if not emailsEnabled then
                return true
            end
            processNewEmails()
        end)
    else
        os.remove(config.files.emails_enable)
        local emailHandler = FindFirstOf("emailHandler_C")
        if emailHandler:IsValid() then
            ExecuteInGameThread(function() 
                emailHandler:K2_DestroyActor()
            end)
        end
        Hint("Twitch Emails disabled")
    end
end

-- Console Commands
RegisterConsoleCommandHandler(("launchChaosBot"), function(full, args)
    launchChaosBot()
    return true
end)

RegisterConsoleCommandHandler(("clearEvents"), function(full, args)
    clearEvents()
    return true
end)

RegisterConsoleCommandHandler(("toggleEmails"), function(full, args)
    toggleEmails()
    return true
end)

RegisterConsoleCommandHandler(("toggleChaosMod"), function(full, args)
    toggleChaosMod()
    return true
end)

RegisterConsoleCommandHandler(("disableChaosMod"), function(full, args)
    disableChaosMod()
    return true
end)

RegisterConsoleCommandHandler(("triggerVote"), function(full, args)
    triggerVoting()
    return true
end)

-- Keybind hooks
RegisterKeyBind(Key.F8, function() toggleChaosMod() end)
RegisterKeyBind(Key.F7, function() triggerVoting() end)
RegisterKeyBind(Key.F6, function() clearEvents() end)
if config.emails.enabled then
    RegisterKeyBind(Key.F3, function() toggleEmails() end)
end

-- Main loop using loopasync
LoopAsync(math.floor(1000 / 30), function()
    if config.chatShop.enabled then
        processNewShopOrders()
    end
end)

LoopAsync(2500, function()
    ExecuteInGameThread(function()
        local findWidget = FindFirstOf("votingMenu_C")
        if findWidget:IsValid() then
            if not findWidget:IsInViewport() and chaosEnabled then
                disableChaosMod()
            end
        end
    end)
end)

print("[ChaosMod] Successfully loaded ChaosMod")


-- Moddy 2024
-- Licensed under Creative Commons Attribution 4.0 International License