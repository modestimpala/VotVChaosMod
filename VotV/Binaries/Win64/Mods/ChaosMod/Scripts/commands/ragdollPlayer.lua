local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        if Pawn:IsValid() then
            local Location = Pawn:K2_GetActorLocation()
            Pawn:ragdollMode(true, false, false)
        else 
            print("Pawn is not valid")
        end
    end
}