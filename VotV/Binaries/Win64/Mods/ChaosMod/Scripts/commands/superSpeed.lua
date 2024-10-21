local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        if Pawn:IsValid() then
            Pawn.defSpeed = 2000
            ExecuteWithDelay(180000, function()
                Pawn.defSpeed = 400
            end)
        else 
            print("Pawn is not valid")
        end
    end
}