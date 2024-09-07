local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local saveSlot = FindFirstOf("saveSlot_C")
        local points = saveSlot.Points
        local mainGame = FindFirstOf("mainGamemode_C")
        local halfPoints = math.floor(points / 2)
        print("Half points: " .. tostring(halfPoints))
        mainGame:AddPoints(-halfPoints)
        return true
    end
}