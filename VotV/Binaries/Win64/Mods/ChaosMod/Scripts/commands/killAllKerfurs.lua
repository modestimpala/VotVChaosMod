local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local kerfurs = FindAllOf("kerfurOmega_2_C")
        if kerfurs then
            for _, kerfur in ipairs(kerfurs) do
                if kerfur:IsValid() then
                    kerfur:attemptIgnite()
                end
            end
        end
        kerfurs = FindAllOf("kerfurOmega_1_C")
        if kerfurs then
            for _, kerfur in ipairs(kerfurs) do
                if kerfur:IsValid() then
                    kerfur:attemptIgnite()
                end
            end
        end
    end
}
