local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers.GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        Pawn.sleepDraining = 10000
        ExecuteWithDelay(5000, function()
            Pawn.sleepDraining = 1
        end)
        return true
    end
}