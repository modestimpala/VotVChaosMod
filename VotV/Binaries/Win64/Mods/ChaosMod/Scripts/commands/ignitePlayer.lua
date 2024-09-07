local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        if Pawn:IsValid() then
            Pawn:ignite(20)
        end
        return true
    end
}