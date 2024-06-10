// Interpolators for handling animations.


// Constructor function for a linear timed decay function.
// The decay function is 1.0 at the start and 0.0 at the end
// and linearly interpolates between the two.
// The decayTime is the time span in milliseconds for the interpolation.
class TimedDecay {
    constructor(decayTime) {
        this.decayTime = decayTime;
        this.startTimestamp = Date.now();
    }
    // Returns the current decay factor.
    getFactor() {
        const now = Date.now();
        const elapsed = now - this.startTimestamp;
        if (elapsed > this.decayTime) {
            return 0.0;
        }
        return (this.decayTime - elapsed) / this.decayTime;
    };

    // Returns the decayed value.
    get(value) {
        return value * this.getFactor();
    }
}

// Constructor function for a squared interpolator.
class SqauredInterpolator {
    get(value) {
        return value * value;
    }
}

// Constructor function for a multipler interpolator.
class MultiplierInterpolator {
    constructor(iterpolarorA, interpolatorB) {
        this.interpolatorA = iterpolarorA;
        this.interpolatorB = interpolatorB;
    }
    
    get(value) {
        return this.interpolatorA.get(value) * this.interpolatorB.get(value);
    }
}


