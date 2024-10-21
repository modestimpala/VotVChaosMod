local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local Scale3D = {X=2, Y=2, Z=2}

        Pawn:SetActorScale3D(Scale3D)
        ExecuteWithDelay(180000, function()
            Pawn:SetActorScale3D({X=1, Y=1, Z=1})
        end)
        return true
    end
}