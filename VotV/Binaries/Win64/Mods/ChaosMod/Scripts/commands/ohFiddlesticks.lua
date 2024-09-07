local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local eventer = FindFirstOf("trigger_eventer_C")
        eventer:runEvent(FText(""), FText(""))
        return true
    end
}