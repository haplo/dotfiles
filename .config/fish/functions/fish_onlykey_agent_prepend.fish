# prepend onlykey-agent to command line
# I use it all the time for SSH access my systems
# https://github.com/trustcrypto/onlykey-agent
function fish_onlykey_agent_prepend
    fish_commandline_prepend "onlykey-agent fidelramos.net --"
end
