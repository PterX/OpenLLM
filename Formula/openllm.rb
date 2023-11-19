# Generated by tools/update-brew-tap.py. DO NOT EDIT!
# Please refers to the original template file Formula/openllm.rb.j2
# vim: set ft=ruby:
class Openllm < Formula
  desc "OpenLLM: Operating LLMs in production"
  homepage "https://github.com/bentoml/OpenLLM"
  version "0.4.16"
  license "Apache-2.0"
  head "https://github.com/bentoml/OpenLLM, branch: main"
  url "https://github.com/bentoml/OpenLLM/archive/v0.4.16.tar.gz"
  sha256 "d0f8d13e12b6beef369886a9869c217c9dee6e4137b1362d5096bddb723cef89"

  on_linux do
    url "https://github.com/bentoml/OpenLLM/releases/download/v0.4.16/openllm-0.4.16-x86_64-unknown-linux-musl.tar.gz"
    sha256 "c728842eef69fe6136dbbb1d38abcce9014e2be89aa73e604e8eb1b398fafdc9"
  end
  on_macos do
    on_arm do
      url "https://github.com/bentoml/OpenLLM/releases/download/v0.4.16/openllm-0.4.16-aarch64-apple-darwin.tar.gz"
      sha256 "25129b5b702056d54c838de64f03c835b0d29a284c0be23b98639351b51d85af"
    end
    on_intel do
      url "https://github.com/bentoml/OpenLLM/releases/download/v0.4.16/openllm-0.4.16-x86_64-apple-darwin.tar.gz"
      sha256 "fa36cb6fea519f59d97835f1a8bed64b5dd7934b198320266aed743c384aeb71"
    end
  end

  def install
    on_linux do
      bin.install "openllm-0.4.16-x86_64-unknown-linux-musl" => "openllm"
    end
  on_macos do
    on_arm do
      bin.install "openllm-0.4.16-aarch64-apple-darwin" => "openllm"
    end
    on_intel do
      bin.install "openllm-0.4.16-x86_64-apple-darwin" => "openllm"
    end
  end
    ohai "To get started, run: 'openllm --help'"
    ohai "To see supported models, run: 'openllm models'"
  end

  test do
    shell_output "#{bin}/openllm --version"
  end
end
