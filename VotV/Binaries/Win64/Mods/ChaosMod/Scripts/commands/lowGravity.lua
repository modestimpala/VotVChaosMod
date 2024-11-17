local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local WorldSettings = FindFirstOf("WorldSettings")
        WorldSettings.bGlobalGravitySet = true
        WorldSettings.GlobalGravityZ = -200
        ExecuteWithDelay(180000, function()
            WorldSettings.bGlobalGravitySet = false
        end)
        return true
    end
}