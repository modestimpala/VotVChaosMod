local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers.GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local saveSlot = FindFirstOf("saveSlot_C")
        saveSlot.food = 100
        return true
    end
}