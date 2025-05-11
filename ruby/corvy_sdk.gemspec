Gem::Specification.new do |spec|
  spec.name          = "corvy_sdk"
  spec.version       = "1.5.1"
  spec.authors       = ["SimuCorps Team"]
  spec.email         = ["contact@simucorps.org"]

  spec.summary       = "Corvy Bot SDK - Client library for building Corvy bots"
  spec.description   = "A Ruby SDK for building bots that interact with the Corvy chat platform"
  spec.homepage      = "https://github.com/SimuCorps/corvy-sdk"
  spec.license       = "MIT"

  spec.files         = Dir["lib/**/*.rb", "README.md", "LICENSE", "corvy_sdk.rb"]
  spec.require_paths = ["lib"]

  spec.required_ruby_version = '>= 2.6.0'

  spec.add_development_dependency "rake", "~> 13.0"
  spec.add_development_dependency "rspec", "~> 3.0"
end 