local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local lights = FindAllOf("ceilingLamp_C")
        local spotlights = {}
        local pointlights = {}
        for _, light in pairs(lights) do
            spotlights[#spotlights + 1] = light.SpotLight
            pointlights[#pointlights + 1] = light.PointLight
        end
        local endtime = os.time() + 60

        LoopAsync(300, function()
            if os.time() < endtime then
                for _, light in pairs(spotlights) do
                    if light:IsValid() then
                        local randomRGB = {R=math.random(), G=math.random(), B=math.random()}
                        light:SetLightColor(randomRGB, false)
                        light:SetIntensity(math.random() * 30000)
                    end
                end
                for _, light in pairs(pointlights) do
                    if light:IsValid() then
                        local randomRGB = {R=math.random(), G=math.random(), B=math.random()}
                        light:SetLightColor(randomRGB, false)
                        light:SetIntensity(math.random() * 80000)
                    end
                end
                return false
            else 
                local whiteRGB = {R=1, G=1, B=1}
                for _, light in pairs(spotlights) do
                    if light:IsValid() then
                        light:SetLightColor(whiteRGB, false)
                        light:SetIntensity(1)
                    end
                end
                for _, light in pairs(pointlights) do
                    if light:IsValid() then
                        light:SetLightColor(whiteRGB, false)
                        light:SetIntensity(1)
                    end
                end
                return true
            end
        end)
        return true
    end
}