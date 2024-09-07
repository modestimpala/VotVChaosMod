-- UE4SS Twitch Chaos Mod (using separate configs)

local json = require("json")  -- Load JSON library
local commands = require("commands")  -- Load commands 
local UEHelpers = require("UEHelpers")  -- Load UEHelpers

-- Define the base path
local base_path = "./pyChaosMod/"
local config_file = base_path .. "config.json"
local emails_path = base_path .. "emails/"
local shops_path = base_path .. "shops/"

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

    RegisterConsoleCommandHandler("lol", function()
        local stuff = FindAllOf("piramid2_C")
        for _, thing in pairs(stuff) do
            thing:K2_DestroyActor()
        end
    end)

    RegisterConsoleCommandHandler("test", function()
        local FirstPlayerController = UEHelpers.GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local obj_C = StaticFindObject("/Game/objects/prop_batts.prop_batts_C")
        local Location = Pawn:K2_GetActorLocation()
        local Rotation = Pawn:K2_GetActorRotation()
        local World = Pawn:GetWorld()
        local obj = World:SpawnActor(obj_C, Location, Rotation, false, nil, nil, false, false)
        obj:playerHandUse_RMB(Pawn)
        return true
    end)

    RegisterConsoleCommandHandler("test2", function()
        local World = UEHelpers:GetWorld()

        local spawn = World:SpawnActor(StaticFindObject("/Game/Mods/ChaosMod/Assets/shopOrderHandler.shopOrderHandler_C"), {}, {}, false, nil, nil, false, false)

        spawn:placeOrderTwitch(FName("Shrimp"), FText("TestUser"))

        ExecuteWithDelay(1000, function()
            spawn:K2_DestroyActor()
        end)

        return true
    end)

    RegisterConsoleCommandHandler("godmode", function()
        local mainGame = FindFirstOf("mainGamemode_C")
        mainGame.Immortal = not mainGame.Immortal
        return true
    end)

    RegisterConsoleCommandHandler("sandbox", function()
        local ui = FindFirstOf("umg_menu_C")
        ui:openSandbox()
    end)

    RegisterConsoleCommandHandler(("Chaos"), function(full, args)
        local command = args[1]
        print("Executing command: " .. command)
        for _, cmd in ipairs(commands_config.commands) do
            if cmd.command == command then
                print("Found command: " .. cmd.command)
                ExecuteCommand(cmd.command)
            end
        end
        return true
    end)

    RegisterConsoleCommandHandler(("PlayerPos"), function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local Location = Pawn:K2_GetActorLocation()
        print(string.format("[MyLuaMod] Player location: {X=%.3f, Y=%.3f, Z=%.3f}\n", Location.X, Location.Y, Location.Z))
        if lastLocation then
            print(string.format("[MyLuaMod] Player moved: {delta_X=%.3f, delta_Y=%.3f, delta_Z=%.3f}\n",
                Location.X - lastLocation.X,
                Location.Y - lastLocation.Y,
                Location.Z - lastLocation.Z)
            )
        end
        lastLocation = Location
        return true
    end)

    RegisterConsoleCommandHandler(("PlayerRot"), function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local Rotation = Pawn:K2_GetActorRotation()
        print(string.format("[MyLuaMod] Player rotation: {Pitch=%.3f, Yaw=%.3f, Roll=%.3f}\n", Rotation.Pitch, Rotation.Yaw, Rotation.Roll))
        return true
    end)

    -- Function to get all files in a directory
    local function getFiles(directory)
        local files = {}
        local p = io.popen('dir "'..directory..'" /b')  -- Windows-specific command
        for file in p:lines() do
            table.insert(files, file)
        end
        p:close()
        return files
    end

    -- Function to process new emails
    local function processNewEmails()
        local files = getFiles(emails_path)
        for _, file in ipairs(files) do
            if file:match("%.json$") then
                local filepath = emails_path .. file
                local email_file = io.open(filepath, "r")
                if email_file then
                    local content = email_file:read("*all")
                    email_file:close()
                    
                    local email_data = json.decode(content)
                    if email_data then
                        print("Processing email: " .. file)
                        
                        -- Find the emailHandler and call addTwitchEmail
                        -- local emailHandler = FindFirstOf("emailHandler_C")
                        local emailHandler = FindFirstOf("emailHandler_C")
                        if not emailHandler:IsValid() then
                            local World = UEHelpers:GetWorld()
                            local emailHandler_C = StaticFindObject("/Game/Mods/ChaosMod/Assets/emailHandler.emailHandler_C")
                            emailHandler = World:SpawnActor(emailHandler_C, {}, {})
                        end
                        if emailHandler and emailHandler:IsValid() then
                            local fullBody = email_data.body .. " - " .. email_data.username
                            emailHandler:addTwitchEmail(FText(email_data.subject), FText(fullBody))
                            print("Email added: " .. email_data.subject .. " - " .. fullBody)
                        else
                            print("Failed to find valid emailHandler_C")
                        end
                        
                        -- Delete the processed email file
                        os.remove(filepath)
                        print("Deleted email file: " .. file)
                    else
                        print("Failed to parse email JSON: " .. file)
                    end
                else
                    print("Failed to open email file: " .. file)
                end
            end
        end
    end

    local function processNewShopOrders()
        local files = getFiles(shops_path)
        for _, file in ipairs(files) do
            if file:match("%.json$") then
                local filepath = shops_path .. file
                local shop_file = io.open(filepath, "r")
                if shop_file then
                    local content = shop_file:read("*all")
                    shop_file:close()
                    
                    local shop_data = json.decode(content)
                    if shop_data then
                        print("Processing shop order: " .. file)
                        
                        -- Find the shopOrderHandler and call placeOrderTwitch
                        local shopHandler = FindFirstOf("shopOrderHandler_C")
                        if not shopHandler:IsValid() then
                            local World = UEHelpers:GetWorld()
                            local shopHandler_C = StaticFindObject("/Game/Mods/ChaosMod/Assets/shopOrderHandler.shopOrderHandler_C")
                            shopHandler = World:SpawnActor(shopHandler_C, {}, {})
                        end
                        if shopHandler and shopHandler:IsValid() then
                            print("Placing order: " .. shop_data.item .. " - " .. shop_data.username)
                            shopHandler:placeOrderTwitch(FName(shop_data.item), FText(shop_data.username))
                            print("Shop order placed: " .. shop_data.item .. " - " .. shop_data.username)
                        else
                            print("Failed to find valid shopOrderHandler_C")
                        end
                        
                        -- Delete the processed shop order file
                        os.remove(filepath)
                        print("Deleted shop order file: " .. file)
                    else
                        print("Failed to parse shop order JSON: " .. file)
                    end
                else
                    print("Failed to open shop order file: " .. file)
                end
            end
        end
    end

    -- Toggle chaos mod
    local function toggleChaosMod()
        chaosEnabled = not chaosEnabled
        if chaosEnabled then
            local file = io.open(config.files.enable, "w")
            file:write("true")
            file:close()
            print("Chaos Mod enabled")
        else
            if os.remove(config.files.enable) then
                print("Removed enable file")
            end
            print("Chaos Mod disabled")
        end
    end

    -- Manually trigger voting
    local function triggerVoting()
        if chaosEnabled then
            print("Triggering vote in overlay application...")
            local file = io.open(config.files.vote_trigger, "w")
            file:write("trigger")
            file:close()
        else
            print("Chaos Mod is not enabled. Enable it first.")
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
                print("Voting ended. Result: " .. result.name)
                
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
                    print("Executing chaos effect(s): " .. result.name)
                    for _, command in ipairs(commands) do
                        ExecuteCommand(command.command)
                    end
                else
                    print("No valid commands found for: " .. result.name)
                end
            end
        end
    end

    local function clearEvents()
        local mainGamemode_C = FindFirstOf("mainGamemode_C")
        if mainGamemode_C:IsValid() then
            print("Clearing events")
            mainGamemode_C.eventsActive:Empty()
            Hint("You can now pause/save")
        else 
            print("Failed to find mainGamemode_C")
        end
    end

    local function toggleEmails()
        emailsEnabled = not emailsEnabled
        if emailsEnabled then
            local file = io.open(config.files.emails_enable, "w")
            file:write("true")
            file:close()
            print("Emails enabled")
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
            if os.remove(config.files.emails_enable) then
                print("Removed emails enable file")
            end
            local emailHandler = FindFirstOf("emailHandler_C")
            if emailHandler:IsValid() then
                print("Destroying emailHandler")
                emailHandler:K2_DestroyActor()
            end
            print("Emails disabled")
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
            if os.remove(config.files.emails_enable) then
                print("Removed emails enable file")
            end
            local emailHandler = FindFirstOf("emailHandler_C")
            if emailHandler:IsValid() then
                print("Destroying emailHandler")
                emailHandler:K2_DestroyActor()
            end
            print("Emails disabled")
            if os.remove(config.files.enable) then
                print("Removed enable file")
            end
            print("Chaos Mod disabled")

        end)
    end)

    ExecuteWithDelay(5000, function()
        local id1, id2
        RegisterHook("/Game/objects/panel_SATconsole.panel_SATconsole_C:actionOptionIndex", function(Context, NewPawn)
            if id1 and id2 then
                UnregisterHook("/Game/Mods/ChaosMod/ModActor.ModActor_C:ToggleChaosMod", id1, id2)
            end
            id1, id2 = RegisterHook("/Game/Mods/ChaosMod/ModActor.ModActor_C:ToggleChaosMod", function()
                toggleChaosMod()
            end)
        end)
    end)

    print("Twitch Chaos Mod and email handler loaded!")
end