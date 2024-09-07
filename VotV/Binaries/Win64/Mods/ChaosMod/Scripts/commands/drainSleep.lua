local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers.GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        Pawn.sleepDraining = 100
        ExecuteWithDelay(13500, function()
            Pawn.sleepDraining = 1
        end)
        return true
    end
}