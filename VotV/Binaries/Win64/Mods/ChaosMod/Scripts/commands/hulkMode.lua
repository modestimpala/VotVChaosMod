local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        if Pawn:IsValid() then
            Pawn.hulkMode = true
            ExecuteWithDelay(180000, function()
                Pawn.hulkMode = false
            end)
        else 
            print("Pawn is not valid")
        end
    end
}