local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        mainGame:deleteActiveSignal()
        return true
    end
}