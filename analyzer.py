import essentia.streaming as ess
import essentia.standard as es
import essentia

def process(audio_file):
    """Tonality of audio"""
    # Initialize algorithms we will use.
    loader = ess.MonoLoader(filename=audio_file)
    framecutter = ess.FrameCutter(frameSize=4096, hopSize=2048, silentFrames='noise')
    windowing = ess.Windowing(type='blackmanharris62')
    spectrum = ess.Spectrum()
    spectralpeaks = ess.SpectralPeaks(orderBy='magnitude',
                                    magnitudeThreshold=0.00001,
                                    minFrequency=20,
                                    maxFrequency=3500,
                                    maxPeaks=60)

    # Use default HPCP parameters for plots.
    # However we will need higher resolution and custom parameters for better Key estimation.

    hpcp = ess.HPCP()
    hpcp_key = ess.HPCP(size=36, # We will need higher resolution for Key estimation.
                        referenceFrequency=440, # Assume tuning frequency is 44100.
                        bandPreset=False,
                        minFrequency=20,
                        maxFrequency=3500,
                        weightType='cosine',
                        nonLinear=False,
                        windowSize=1.)

    key = ess.Key(profileType='edma', # Use profile for electronic music.
                numHarmonics=4,
                pcpSize=36,
                slope=0.6,
                usePolyphony=True,
                useThreeChords=True)

    # Use pool to store data.
    pool = essentia.Pool()

    # Connect streaming algorithms.
    loader.audio >> framecutter.signal
    framecutter.frame >> windowing.frame >> spectrum.frame
    spectrum.spectrum >> spectralpeaks.spectrum
    spectralpeaks.magnitudes >> hpcp.magnitudes
    spectralpeaks.frequencies >> hpcp.frequencies
    spectralpeaks.magnitudes >> hpcp_key.magnitudes
    spectralpeaks.frequencies >> hpcp_key.frequencies
    hpcp_key.hpcp >> key.pcp
    hpcp.hpcp >> (pool, 'tonal.hpcp')
    key.key >> (pool, 'tonal.key_key')
    key.scale >> (pool, 'tonal.key_scale')
    key.strength >> (pool, 'tonal.key_strength')

    # Run streaming network.
    essentia.run(loader)


    """BPM by TempoCNN"""
    sr = 11025
    audio_11khz = es.MonoLoader(filename=audio_file, sampleRate=sr)()

    global_bpm, local_bpm, local_probs = es.TempoCNN(graphFilename='./deeptemp-k16-3.pb')(audio_11khz)


    """Chords"""
    chords, strength = es.ChordsDetection(hopSize=2048, windowSize=2)(pool['tonal.hpcp'])

    def _remove_consecutive_duplicates(lst):
        result = []
        prev_element = None
        for element in lst:
            if element != prev_element:
                result.append(element)
                prev_element = element
        return result
    chords = _remove_consecutive_duplicates(chords)


    if __name__ == "__main__":
        """Print Result"""
        print("Estimated key and scale:", pool['tonal.key_key'] + " " + pool['tonal.key_scale'])
        print(f'song BPM: {global_bpm}')
        print(chords)
    tonality = pool['tonal.key_key'] + " " + pool['tonal.key_scale']
    return tonality, global_bpm, chords