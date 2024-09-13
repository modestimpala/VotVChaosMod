local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local World = Pawn:GetWorld()

        local mainGamemode_C = FindFirstOf("mainGamemode_C")
        if mainGamemode_C:IsValid() then
            local save = mainGamemode_C.saveSlot

            if save:IsValid() then
                save.food = 100
            end
        end
        return true
    end
}