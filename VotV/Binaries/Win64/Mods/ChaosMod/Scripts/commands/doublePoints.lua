local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local saveSlot = FindFirstOf("saveSlot_C")
        local points = saveSlot.Points
        local mainGame = FindFirstOf("mainGamemode_C")
        mainGame:AddPoints(points * 2)
        return true
    end
}