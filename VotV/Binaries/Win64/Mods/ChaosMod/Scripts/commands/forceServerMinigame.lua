local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        local out = {}
        mainGame:launchServerMinigame(out)
        mainGame.serverMinigame = out[0]
        return true
    end
}