local json = require("json")  -- Load JSON library

-- Define the base path
local base_path = "./pyChaosMod/"

-- Function to safely write to a file
function safeWriteToFile(filePath, content)
    local file = io.open(filePath, "w")
    if file then
        file:write(content)
        file:close()
        print("Successfully wrote to " .. filePath)
    else
        print("Failed to open file for writing: " .. filePath)
    end
end

-- Function to safely remove a file
function safeRemoveFile(filePath)
    if os.remove(filePath) then
        print("Successfully removed " .. filePath)
    else
        print("Failed to remove file (may not exist): " .. filePath)
    end
end

-- Function to read config files
function readConfig(filename)
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

-- Function to read the master JSON file
function readMasterFile(filepath)
    local file = io.open(filepath, "r")
    if not file then return {} end
    local content = file:read("*all")
    file:close()
    return json.decode(content) or {}
end

-- Function to write the master JSON file
function writeMasterFile(filepath, data)
    local file = io.open(filepath, "w")
    file:write(json.encode(data))
    file:close()
end

-- Function to download and extract ChaosBot
function downloadAndExtractChaosBot(base_path)
    local findUI = FindFirstOf("menuChaos_C")
    if findUI:IsValid() then
        findUI:downloadStarted()
    end

    local zipUrl = "https://github.com/modestimpala/VotVChaosMod/releases/download/latest/ChaosBot.zip"
    local zipPath = base_path .. "ChaosBot.zip"

    -- Download the zip file
    print("Attempting to download ChaosBot")
    local downloadCommand = string.format('powershell -command "(New-Object Net.WebClient).DownloadFile(\'%s\', \'%s\')"', zipUrl, zipPath)
    local downloadSuccess = os.execute(downloadCommand)

    if not downloadSuccess then
        print("Failed to download ChaosBot")
        return false
    end

    print("Download successful")

    -- Extract the zip file
    local extractCommand = string.format('powershell -command "Expand-Archive -Path \'%s\' -DestinationPath \'%s\' -Force"', zipPath, base_path)
    local extractSuccess = os.execute(extractCommand)

    if not extractSuccess then
        print("Failed to extract zip file")
        os.remove(zipPath)
        return false
    end

    print("Extraction successful")

    -- Clean up the zip file
    os.remove(zipPath)
    return true
end

function launchChaosBot()
    -- Ensure base_path directory exists
    local createDirCommand = string.format('if not exist "%s" mkdir "%s"', base_path, base_path)
    local dirCreationSuccess = os.execute(createDirCommand)

    if not dirCreationSuccess then
        print("Failed to create directory: " .. base_path)
        return
    end

    local exePath = base_path .. "ChaosBot.exe"
    local scriptPath = base_path .. "ChaosBot.py"

    -- Try to launch the executable
    local file = io.open(exePath, "r")
    if file then
        file:close()
        print("Attempting to launch executable: " .. exePath)
        local success, err, code = os.execute(string.format('start "" "%s"', exePath))
        
        if success then
            print("Executable opened successfully: " .. exePath)
            return
        else
            print("Failed to open executable: " .. (err or "Unknown error"))
        end
    else
        print("Executable not found: " .. exePath)
    end

    -- If executable failed or not found, try Python script
    print("Trying to open with python")
    local pyFile = io.open(scriptPath, "r")
    if pyFile then
        pyFile:close()
        local success, err, code = os.execute(string.format('start "" python "%s"', scriptPath))
        
        if success then
            print("Python script opened successfully: " .. scriptPath)
            return
        else
            print("Failed to open python script: " .. (err or "Unknown error"))
        end
    else
        print("Python script not found: " .. scriptPath)
    end

    -- If both executable and Python script failed, download the executable
    print("Both executable and Python script not found or failed to launch")
    if downloadAndExtractChaosBot(base_path) then
        print("Attempting to launch newly downloaded executable")
        local success, err, code = os.execute(string.format('start "" "%s"', exePath))
        
        if success then
            print("Executable opened successfully after download: " .. exePath)
        else
            print("Failed to open executable after download: " .. (err or "Unknown error"))
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
        print("Failed to download and extract ChaosBot")
    end
end