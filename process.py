import argparse
import soundfile as sf
import matplotlib.pyplot as plt
import numpy as np
import pvkoala
import wave
import struct

PROGRESS_BAR_LENGTH = 30

def plot_audio(infile, outfile):
    raw_data, samplerate = sf.read(infile)
    processed_data, samplerate = sf.read(outfile)
    duration = len(raw_data) / samplerate
    time = np.linspace(0, duration, len(raw_data))

    fig, axs = plt.subplots(2, 1, figsize=(10, 8))

    axs[0].plot(time, raw_data)
    axs[0].set_xlabel('t')
    axs[0].set_ylabel('Amplitude')
    axs[0].set_title('Raw Audio')
    axs[0].grid(True)

    axs[1].plot(time, processed_data)
    axs[1].set_xlabel('t')
    axs[1].set_ylabel('Amplitude')
    axs[1].set_title('With Noise Suppression')
    axs[1].grid(True)

    plt.tight_layout()
    plt.show()

def suppress_noise(infile, outfile):
    koala = pvkoala.create("oAPNEIVZbMGi2xl/cTuWV9mvG49C6g8jMbKrtqSeywhEG/vD3KSc+Q==")
    length_sec = 0.0
    try:
        with wave.open(infile) as input_file:
            if input_file.getframerate() != koala.sample_rate:
                raise ValueError('Invalid sample rate of `%d`. Koala only accepts `%d`' % (
                    input_file.getframerate(),
                    koala.sample_rate))
            if input_file.getnchannels() != 1:
                raise ValueError('This demo can only process single-channel WAV files')
            if input_file.getsampwidth() != 2:
                raise ValueError('This demo can only process WAV files with 16-bit PCM encoding')
            input_length = input_file.getnframes()

            with wave.open(outfile, 'wb') as output_file:
                output_file.setnchannels(1)
                output_file.setsampwidth(2)
                output_file.setframerate(koala.sample_rate)

                start_sample = 0
                while start_sample < input_length + koala.delay_sample:
                    end_sample = start_sample + koala.frame_length

                    frame_buffer = input_file.readframes(koala.frame_length)
                    num_samples_read = len(frame_buffer) // struct.calcsize('h')
                    input_frame = struct.unpack('%dh' % num_samples_read, frame_buffer)
                    if num_samples_read < koala.frame_length:
                        input_frame = input_frame + (0,) * (koala.frame_length - num_samples_read)

                    output_frame = koala.process(input_frame)

                    if end_sample > koala.delay_sample:
                        if end_sample > input_length + koala.delay_sample:
                            output_frame = output_frame[:input_length + koala.delay_sample - start_sample]
                        if start_sample < koala.delay_sample:
                            output_frame = output_frame[koala.delay_sample - start_sample:]
                        output_file.writeframes(struct.pack('%dh' % len(output_frame), *output_frame))
                        length_sec += len(output_frame) / koala.sample_rate

                    start_sample = end_sample
                    progress = start_sample / (input_length + koala.delay_sample)
                    bar_length = int(progress * PROGRESS_BAR_LENGTH)
                    print(
                        '\r[%3d%%]|%s%s|' % (
                            progress * 100,
                            '#' * bar_length,
                            ' ' * (PROGRESS_BAR_LENGTH - bar_length)),
                        end='',
                        flush=True)

                print()

    except KeyboardInterrupt:
        print()
    except pvkoala.KoalaActivationLimitError:
        print('AccessKey has reached its processing limit')
    finally:
        if length_sec > 0:
            print('%.2f seconds of audio have been written to %s.' % (length_sec, outfile))

        koala.delete()

def main():
    parser = argparse.ArgumentParser(description='plot waveform')
    parser.add_argument('filename', type=str, help='file path')
    args = parser.parse_args()

    infile = args.filename
    outfile = "out.wav"

    suppress_noise(infile, outfile)
    plot_audio(infile, outfile)

if __name__ == '__main__':
    main()
