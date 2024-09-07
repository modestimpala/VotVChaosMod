local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        mainGame:addEffect(FName("nausea"), 50, 45, false, false)
        return true
    end
}