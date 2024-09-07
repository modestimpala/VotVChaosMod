local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local FirstPlayerController = UEHelpers:GetPlayerController()
        local Pawn = FirstPlayerController.Pawn
        local endTime = os.time() + 30
        LoopAsync(100, function()
            if os.time() < endTime then
                Pawn:flashlightUse()
                return false
            else
                return true
            end
        end)
        return true
    end
}