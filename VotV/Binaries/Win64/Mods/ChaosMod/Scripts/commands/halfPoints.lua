local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local World = Pawn:GetWorld()

        local mainGamemode_C = FindFirstOf("mainGamemode_C")
        if mainGamemode_C:IsValid() then
            local save = mainGamemode_C.saveSlot
            local points = 0
            if save:IsValid() then
                points = save.points
            end
            local halfPoints = math.floor(points / 2)
            mainGamemode_C:AddPoints(-halfPoints)
        end
        return true
    end
}